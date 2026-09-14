# FlyBody GLB

Source: https://github.com/TuragaLab/flybody
Commit: d015e9bfe441bd90ae431bac24c55cb74bdbce26
Original files: flybody/fruitfly/assets/fruitfly.xml and its 85 OBJ visual meshes.
License: Apache-2.0; reproduced in FlyBody-LICENSE.
Developed by Google DeepMind and HHMI Janelia; see the upstream publication and attribution.

The local converter `tools/convert_flybody.py` preserves named body hierarchies, positions,
quaternions, mesh scale and material assignments. It recalculates smooth normals and packs
the visual geometries into `flybody.glb`. Rendering recolors the materials and animates
named leg/wing/head nodes. This is an artistic joint animation, not MuJoCo's physics or a
scientifically fitted walking controller. The body is displayed larger for easy observation.
The original raster sprite is retained in assets for compatibility but is not used by the 3D renderer.
