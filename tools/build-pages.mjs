import {cp,mkdir,readFile,rm,writeFile} from 'node:fs/promises';
const out=new URL('../dist/',import.meta.url),web=new URL('../web/',import.meta.url),three=new URL('../node_modules/three/',import.meta.url);
await rm(out,{recursive:true,force:true});await mkdir(out,{recursive:true});
for(const name of ['main.js','style.css','demo-api.js'])await cp(new URL(name,web),new URL(name,out));
await mkdir(new URL('assets/',out),{recursive:true});await cp(new URL('../assets/flybody.glb',import.meta.url),new URL('assets/flybody.glb',out));
for(const dir of ['vendor/three/build/','vendor/three/examples/jsm/controls/','vendor/three/examples/jsm/environments/','vendor/three/examples/jsm/loaders/','vendor/three/examples/jsm/utils/'])await mkdir(new URL(dir,out),{recursive:true});
for(const name of ['three.module.min.js','three.core.min.js'])await cp(new URL('build/'+name,three),new URL('vendor/three/build/'+name,out));
for(const name of ['controls/OrbitControls.js','environments/RoomEnvironment.js','loaders/GLTFLoader.js','utils/BufferGeometryUtils.js'])await cp(new URL('examples/jsm/'+name,three),new URL('vendor/three/examples/jsm/'+name,out));
let html=await readFile(new URL('index.html',web),'utf8');html=html.replace('href="/web/style.css"','href="./style.css"')
 .replace('"three":"/node_modules/three/build/three.module.js","three/addons/":"/node_modules/three/examples/jsm/"','"three":"./vendor/three/build/three.module.min.js","three/addons/":"./vendor/three/examples/jsm/"')
 .replace('<script type="module" src="/web/main.js"></script>','<script src="./demo-api.js"></script><script type="module" src="./main.js"></script>');
await writeFile(new URL('index.html',out),html.replace('/assets/flybody.glb','./assets/flybody.glb'));await writeFile(new URL('.nojekyll',out),'');console.log('Built Cyberfly browser demo in dist/');
