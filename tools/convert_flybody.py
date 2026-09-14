"""Convert Apache-2.0 FlyBody MJCF visual meshes to a self-contained GLB.
Usage: python tools/convert_flybody.py SOURCE_ASSETS
Preserves body/geom transforms and original material assignments. No MuJoCo needed.
"""
import json
import struct
import sys
from pathlib import Path
import xml.etree.ElementTree as ET
import numpy as np

source = Path(sys.argv[1])
root = ET.parse(source / 'fruitfly.xml').getroot()
doc = {'asset': {'version': '2.0', 'generator': 'Cyberfly FlyBody converter',
                 'copyright': 'FlyBody / TuragaLab, Apache-2.0'},
       'scene': 0, 'scenes': [{'nodes': [0]}], 'nodes': [], 'meshes': [],
       'materials': [], 'accessors': [], 'bufferViews': [], 'buffers': []}
binary = bytearray()

def accessor(a, kind, target):
    a = np.ascontiguousarray(a)
    while len(binary) % 4: binary.append(0)
    offset = len(binary)
    binary.extend(a.tobytes())
    vi = len(doc['bufferViews'])
    doc['bufferViews'].append({'buffer': 0, 'byteOffset': offset, 'byteLength': a.nbytes, 'target': target})
    item = {'bufferView': vi, 'componentType': 5126 if a.dtype == np.float32 else 5125,
            'count': len(a), 'type': kind}
    if kind == 'VEC3':
        item.update(min=a.min(axis=0).tolist(), max=a.max(axis=0).tolist())
    doc['accessors'].append(item)
    return len(doc['accessors']) - 1

materials = {}
for m in root.findall('asset/material'):
    rgba = list(map(float, m.get('rgba', '0.5 0.3 0.1 1').split()))
    name = m.get('name')
    if name == 'black': rgba[:3] = [0.025, 0.013, 0.007]
    mat = {'name': name, 'doubleSided': True,
           'pbrMetallicRoughness': {'baseColorFactor': rgba, 'metallicFactor': 0.05,
                                    'roughnessFactor': 0.33 if name == 'red' else 0.56}}
    if rgba[3] < 1:
        mat['alphaMode'] = 'BLEND'
        mat['pbrMetallicRoughness']['roughnessFactor'] = 0.18
    materials[name] = len(doc['materials'])
    doc['materials'].append(mat)

mesh_files = {m.get('name'): source / m.get('file') for m in root.findall('asset/mesh')}
geometry = {}
def read_obj(name):
    if name in geometry: return geometry[name]
    verts, faces = [], []
    for line in mesh_files[name].read_text().splitlines():
        parts = line.split()
        if not parts: continue
        if parts[0] == 'v': verts.append([float(x) * .1 for x in parts[1:4]])
        elif parts[0] == 'f':
            ids = [int(x.split('/')[0]) for x in parts[1:]]
            ids = [(i - 1 if i > 0 else len(verts) + i) for i in ids]
            faces.extend([[ids[0], ids[j], ids[j+1]] for j in range(1, len(ids)-1)])
    v, f = np.array(verts, np.float32), np.array(faces, np.uint32)
    normals = np.zeros_like(v)
    face_normals = np.cross(v[f[:,1]] - v[f[:,0]], v[f[:,2]] - v[f[:,0]])
    for col in range(3): np.add.at(normals, f[:,col], face_normals)
    normals /= np.maximum(np.linalg.norm(normals, axis=1, keepdims=True), 1e-12)
    geometry[name] = {'attributes': {'POSITION': accessor(v, 'VEC3', 34962),
                                     'NORMAL': accessor(normals, 'VEC3', 34962)},
                      'indices': accessor(f.reshape(-1), 'SCALAR', 34963)}
    return geometry[name]

def node_for(element):
    n = {'name': element.get('name', 'part')}
    if element.get('pos'): n['translation'] = list(map(float, element.get('pos').split()))
    if element.get('quat'):
        w, x, y, z = map(float, element.get('quat').split())
        q = np.array([x,y,z,w]); q /= np.linalg.norm(q)
        n['rotation'] = q.tolist()
    return n

doc['nodes'].append({'name': 'FlyBody_Z_to_Y', 'rotation': [-.7071067811865475, 0, 0, .7071067811865476], 'children': []})
def body(el, parent):
    n = node_for(el); n['children'] = []
    idx = len(doc['nodes']); doc['nodes'].append(n); doc['nodes'][parent]['children'].append(idx)
    for g in el.findall('geom'):
        mesh = g.get('mesh')
        if not mesh: continue
        part = node_for(g)
        primitive = dict(read_obj(mesh)); primitive['material'] = materials[g.get('material','body')]
        part['mesh'] = len(doc['meshes'])
        doc['meshes'].append({'name': mesh, 'primitives': [primitive]})
        gi = len(doc['nodes']); doc['nodes'].append(part); n['children'].append(gi)
    for child in el.findall('body'): body(child, idx)

for el in root.findall('worldbody/body'): body(el, 0)
while len(binary) % 4: binary.append(0)
doc['buffers'] = [{'byteLength': len(binary)}]
js = json.dumps(doc, separators=(',', ':')).encode()
js += b' ' * ((-len(js)) % 4)
output = Path(__file__).resolve().parents[1] / 'assets' / 'flybody.glb'
output.write_bytes(struct.pack('<III', 0x46546C67, 2, 12+8+len(js)+8+len(binary)) +
                   struct.pack('<II', len(js), 0x4E4F534A) + js +
                   struct.pack('<II', len(binary), 0x004E4942) + binary)
print(f'{output}: {len(doc["meshes"])} meshes, {len(doc["nodes"])} nodes, {output.stat().st_size/1e6:.1f} MB')
