import * as T from 'three';
import {OrbitControls} from 'three/addons/controls/OrbitControls.js';
import {GLTFLoader} from 'three/addons/loaders/GLTFLoader.js';
import {RoomEnvironment} from 'three/addons/environments/RoomEnvironment.js';

const $=id=>document.getElementById(id);
const renderer=new T.WebGLRenderer({antialias:true,alpha:false});
renderer.setPixelRatio(Math.min(devicePixelRatio,1.5));renderer.setSize(innerWidth,innerHeight);
renderer.shadowMap.enabled=true;renderer.shadowMap.type=T.PCFSoftShadowMap;
renderer.toneMapping=T.ACESFilmicToneMapping;renderer.toneMappingExposure=.95;
$('viewport').appendChild(renderer.domElement);
const scene=new T.Scene();scene.background=new T.Color('#d9dfd2');scene.fog=new T.Fog('#d9dfd2',25,65);
const camera=new T.PerspectiveCamera(38,innerWidth/innerHeight,.03,150);
const controls=new OrbitControls(camera,renderer.domElement);controls.enableDamping=true;controls.dampingFactor=.08;
controls.minDistance=1.6;controls.maxDistance=45;controls.maxPolarAngle=Math.PI*.485;
const pmrem=new T.PMREMGenerator(renderer);scene.environment=pmrem.fromScene(new RoomEnvironment(),.04).texture;pmrem.dispose();
scene.environmentIntensity=.5;
scene.add(new T.HemisphereLight('#ecf1db','#566041',.85));
const sun=new T.DirectionalLight('#fff3d5',2.3);sun.position.set(6,16,4);sun.castShadow=true;
sun.shadow.mapSize.set(2048,2048);Object.assign(sun.shadow.camera,{left:-17,right:17,top:17,bottom:-17,near:.5,far:50});
sun.shadow.bias=-.00025;sun.shadow.normalBias=.025;scene.add(sun);scene.add(sun.target);
const habitat=new T.Group();scene.add(habitat);const flyRoot=new T.Group();scene.add(flyRoot);
const sphere=new T.SphereGeometry(1,24,16);const rockGeo=new T.IcosahedronGeometry(1,1);
const mats={soil:new T.MeshStandardMaterial({color:'#9b9873',roughness:1}),
 stone:new T.MeshStandardMaterial({color:'#989c88',roughness:.91}),
 bark:new T.MeshStandardMaterial({color:'#755337',roughness:.94}),
 leaf:new T.MeshStandardMaterial({color:'#54854c',roughness:.6,side:T.DoubleSide}),
 leafLight:new T.MeshStandardMaterial({color:'#86a959',roughness:.68,side:T.DoubleSide}),
 water:new T.MeshPhysicalMaterial({color:'#547f73',roughness:.12,metalness:.12,transparent:true,opacity:.82,clearcoat:1}),
 banana:new T.MeshStandardMaterial({color:'#e4c64d',roughness:.52}),
 cut:new T.MeshStandardMaterial({color:'#eedfaf',roughness:.88}),
 vein:new T.MeshStandardMaterial({color:'#a9bd76',roughness:.8}),
 rim:new T.MeshStandardMaterial({color:'#5c6754',roughness:.8})};
function mesh(g,m,parent,pos=[0,0,0],scale=[1,1,1]){const o=new T.Mesh(g,m);o.position.set(...pos);o.scale.set(...scale);o.castShadow=true;o.receiveShadow=true;parent.add(o);return o;}
function tube(points,r,mat,parent){return mesh(new T.TubeGeometry(new T.CatmullRomCurve3(points.map(p=>new T.Vector3(...p))),14,r,6,false),mat,parent);}
let seed=1;function rand(){seed=(seed*1664525+1013904223)>>>0;return seed/4294967296;}
function soilTexture(){const c=document.createElement('canvas');c.width=c.height=512;const ctx=c.getContext('2d');ctx.fillStyle='#a19c79';ctx.fillRect(0,0,512,512);seed=21;
 for(let i=0;i<28000;i++){let a=rand(),r=rand()*1.8;ctx.fillStyle=`rgba(${a>.5?'55,61,36':'231,217,164'},${rand()*.24})`;ctx.beginPath();ctx.ellipse(rand()*512,rand()*512,r,r*.7,0,0,7);ctx.fill();}
 const t=new T.CanvasTexture(c);t.wrapS=t.wrapT=T.RepeatWrapping;t.repeat.set(10,8);t.colorSpace=T.SRGBColorSpace;t.anisotropy=4;return t;}
mats.soil.map=soilTexture();mats.soil.bumpMap=mats.soil.map;mats.soil.bumpScale=.055;
const foodGroup=new T.Group();scene.add(foodGroup);
function leafGeometry(length,width,bend){const p=[],uv=[],idx=[];for(let i=0;i<=12;i++){const t=i/12,w=Math.sin(Math.PI*t)**.8*width;for(let j=0;j<3;j++){const x=(j-1)*w;p.push(x,Math.sin(t*Math.PI)*bend-Math.abs(x)*.13,t*length);uv.push(j/2,t);}}for(let i=0;i<12;i++)for(let j=0;j<2;j++){const k=i*3+j;idx.push(k,k+3,k+1,k+1,k+3,k+4);}const g=new T.BufferGeometry();g.setAttribute('position',new T.Float32BufferAttribute(p,3));g.setAttribute('uv',new T.Float32BufferAttribute(uv,2));g.setIndex(idx);g.computeVertexNormals();return g;}
function plant(obj,parent){const g=new T.Group();g.position.set(obj.x,0,obj.y);parent.add(g);const h=obj.height*1.15;
 tube([[0,0,0],[.03,h*.5,.02],[0,h,0]],.018,mats.bark,g);
 for(let i=0;i<8;i++){const layer=new T.Group();layer.position.y=.15+i*h*.09;layer.rotation.y=i*2.399;layer.rotation.x=-.18;g.add(layer);const len=.7*(1-i*.035);mesh(leafGeometry(len,.22,.16),i%2?mats.leaf:mats.leafLight,layer);tube([[0,.01,0],[0,.17,len*.5],[0,0,len]],.004,mats.vein,layer);}}
function banana(f,parent){const g=new T.Group();g.position.set(f.x,.12,f.y);g.rotation.y=f.x*1.7;parent.add(g);
 tube([[-.45,.10,0],[-.2,0,0],[.1,-.015,0],[.4,.1,0],[.55,.26,0]],.12,mats.banana,g);
 mesh(new T.CylinderGeometry(.085,.085,.015,24),mats.cut,g,[-.44,.1,0]).rotation.z=Math.PI/2;
 tube([[.54,.24,0],[.58,.32,0]],.04,mats.bark,g);
 for(let i=0;i<9;i++)mesh(sphere,mats.bark,g,[-.3+i*.085,.105+Math.abs(i-4)*.012,.045],[.008,.003,.011]);}
let mapData,foodsKey='',lastRevision=-1;
function clearGroup(g){while(g.children.length){const obj=g.children[0];g.remove(obj);obj.traverse(o=>{if(o.isMesh && o.geometry!==sphere && o.geometry!==rockGeo)o.geometry.dispose();});}}
function rebuildFoods(foods){const key=JSON.stringify(foods);if(key===foodsKey)return;foodsKey=key;clearGroup(foodGroup);foods.forEach(f=>banana(f,foodGroup));}
function buildWorld(data){mapData=data;lastRevision=data.revision;clearGroup(habitat);const w=data.grid[0].length,h=data.grid.length;
 mesh(new T.BoxGeometry(w,.45,h),mats.rim,habitat,[w/2,-.29,h/2]);const floor=mesh(new T.PlaneGeometry(w,h),mats.soil,habitat,[w/2,-.055,h/2]);floor.rotation.x=-Math.PI/2;floor.castShadow=false;
 seed=117;
 // Pebbles and ground litter are instanced to keep draw calls low on integrated graphics.
 const pebbles=new T.InstancedMesh(rockGeo,mats.stone,850);pebbles.receiveShadow=true;
 const matrix=new T.Matrix4(),q=new T.Quaternion(),sc=new T.Vector3();
 for(let i=0;i<850;i++){let x=1+rand()*(w-2),z=1+rand()*(h-2),r=.02+rand()*.055;q.setFromEuler(new T.Euler(rand()*2,rand()*6,0));sc.set(r,r*.55,r*.7);matrix.compose(new T.Vector3(x,0,z),q,sc);pebbles.setMatrixAt(i,matrix);pebbles.setColorAt(i,new T.Color().setHSL(.13+rand()*.05,.1+rand()*.12,.3+rand()*.25));}habitat.add(pebbles);
 for(let z=0;z<h;z++)for(let x=0;x<w;x++)if(data.grid[z][x]==='#'){
   const edge=x===0||z===0||x===w-1||z===h-1;
   if(edge){mesh(new T.BoxGeometry(1,.32,1),mats.rim,habitat,[x+.5,.08,z+.5]);continue;}
   for(let i=0;i<3;i++){const r=mesh(rockGeo,mats.stone,habitat,[x+.3+rand()*.4,.25+i*.12,z+.3+rand()*.4],[.45,.35,.46]);r.rotation.set(rand(),rand()*6,rand()*.4);}}
 for(const o of data.decor){if(o.kind==='plant'){plant(o,habitat);continue;}if(o.kind==='rock'){const r=mesh(new T.IcosahedronGeometry(1,2),mats.stone,habitat,[o.x,o.height*.42,o.y],[o.radius,o.height*.65,o.radius*.86]);r.rotation.y=o.x;}
 if(o.kind==='stump'){mesh(new T.CylinderGeometry(o.radius*.85,o.radius,o.height,16),mats.bark,habitat,[o.x,o.height*.5,o.y]);mesh(new T.CylinderGeometry(o.radius*.82,o.radius*.82,.01,32),mats.cut,habitat,[o.x,o.height+.004,o.y]);for(let i=1;i<5;i++){let ring=mesh(new T.TorusGeometry(o.radius*i/6,.005,3,32),mats.bark,habitat,[o.x,o.height+.012,o.y]);ring.rotation.x=Math.PI/2;}}
 if(o.kind==='puddle'){let puddle=mesh(new T.CircleGeometry(o.radius,48),mats.water,habitat,[o.x,.002,o.y],[1, .8,1]);puddle.rotation.x=-Math.PI/2;puddle.castShadow=false;for(let i=0;i<12;i++){const a=i/12*Math.PI*2;mesh(rockGeo,mats.stone,habitat,[o.x+Math.cos(a)*o.radius,.04,o.y+Math.sin(a)*o.radius*.8],[.11,.08,.08]);}}}
 rebuildFoods(data.foods);
}
let flyModel,animated=[],flySize=1,latest,frameCount=0,lastFps=performance.now(),edit=false,selectedTool='food',follow=true;
const loader=new GLTFLoader();
loader.load('/assets/flybody.glb',gltf=>{
 flyModel=gltf.scene;flyRoot.add(flyModel);
 const palette={body:'#855329',lower:'#b78348',red:'#a92b13',brown:'#533018',black:'#1a130f','bristle-brown':'#29180d',ocelli:'#32160d',membrane:'#c8d7d2'};
 flyModel.traverse(o=>{if(o.isMesh){o.castShadow=true;o.receiveShadow=true;
   const mat=o.material;if(palette[mat.name])mat.color.set(palette[mat.name]);
   if(mat.name==='membrane'){mat.depthWrite=false;mat.opacity=.32;o.castShadow=false;}
 }});
 let box=new T.Box3().setFromObject(flyModel);const size=box.getSize(new T.Vector3());flySize=1.6/Math.max(size.x,size.z);flyModel.scale.setScalar(flySize);box=new T.Box3().setFromObject(flyModel);flyModel.position.y=-box.min.y+.02;
 flyModel.traverse(o=>{if(o.children.length && /^(coxa|femur|tibia)_T[123]_(left|right)$|^wing_(left|right)$|^head$/.test(o.name))animated.push({node:o,base:o.quaternion.clone(),name:o.name});});
 window.modelReport={meshes:0,vertices:0,size:size.toArray(),animated:animated.map(x=>x.name)};flyModel.traverse(o=>{if(o.isMesh){window.modelReport.meshes++;window.modelReport.vertices+=o.geometry.attributes.position.count;}});
 $('status').textContent='GLB 模型加载完成';
},undefined,e=>toast('果蝇模型加载失败：'+e.message));
const pathMat=new T.LineBasicMaterial({color:'#719a72',transparent:true,opacity:.6});let pathLine;
function toast(t){$('toast').textContent=t;$('toast').style.opacity=1;clearTimeout(window.toastTimer);window.toastTimer=setTimeout(()=>$('toast').style.opacity=0,3500);}
async function command(d){const r=await fetch('/api/command',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)});const j=await r.json();if(!r.ok)throw Error(j.error);return j;}
async function poll(){try{latest=await (await fetch('/api/state')).json();if(lastRevision!==latest.revision)buildWorld(await(await fetch('/api/world')).json());rebuildFoods(latest.foods);
 $('status').textContent=latest.error?latest.error:latest.status==='warming'?'神经模型预热中':latest.status==='preview'?'画面预览 · 无神经模拟':latest.status==='demo'?(latest.paused?'在线演示已暂停':'在线轻量闭环运行中'):latest.paused?'模拟已暂停':'全脑闭环运行中';
 const states={'exploring':'探索','feeding':'接触食物','escaping':'逃逸','avoiding':'接近障碍','tracking food':'接近食物'};
 $('behavior').textContent=states[latest.fly.state]||latest.fly.state;$('simtime').textContent=latest.time.toFixed(2)+' s';$('ms').textContent=latest.stats.step_ms?latest.stats.step_ms.toFixed(1)+' ms':'—';$('active').textContent=latest.status==='preview'?'—':(latest.stats.active||0).toLocaleString();$('food').textContent=latest.fly.foods_found+' / '+(latest.foods.length+latest.fly.foods_found);
 $('play').textContent=latest.paused?'开始探索':'暂停探索';
 for(const [k,id] of [['steer_L','left'],['steer_R','right']]){const v=latest.stats[k]||0;$(id+'value').textContent=v.toFixed(1)+' Hz';$(id+'bar').style.width=Math.min(v/20*100,100)+'%';}
 if(pathLine){scene.remove(pathLine);pathLine.geometry.dispose();}pathLine=new T.Line(new T.BufferGeometry().setFromPoints(latest.trail.map(p=>new T.Vector3(p[0],.01,p[1]))),pathMat);pathLine.visible=$('trail').checked;scene.add(pathLine);
 }catch(e){$('status').textContent='本地服务连接中断';}setTimeout(poll,110);}
const startMap=await(await fetch('/api/world')).json();buildWorld(startMap);latest=await(await fetch('/api/state')).json();
flyRoot.position.set(latest.fly.x,0,latest.fly.y);controls.target.copy(flyRoot.position).add(new T.Vector3(0,.3,0));camera.position.copy(controls.target).add(new T.Vector3(5.2,3.8,5.0));controls.update();poll();
function cameraView(mode){const p=flyRoot.position.clone().add(new T.Vector3(0,.35,0));controls.target.copy(p);camera.position.copy(p).add(mode==='macro'?new T.Vector3(2.0,1.0,1.7):mode==='overview'?new T.Vector3(15,19,15):new T.Vector3(5.2,3.8,5));follow=mode!=='overview';for(const k of ['follow','macro','overview'])$(k).classList.toggle('selected',k===mode);}
for(const k of ['follow','macro','overview'])$(k).onclick=()=>cameraView(k);
$('play').onclick=()=>command({action:'pause',value:!latest.paused}).catch(e=>toast(e.message));
$('shadows').onchange=()=>renderer.shadowMap.enabled=$('shadows').checked;
const cursor=mesh(new T.PlaneGeometry(.98,.98),new T.MeshBasicMaterial({color:'#b9dc90',transparent:true,opacity:.55,side:T.DoubleSide}),scene);cursor.rotation.x=-Math.PI/2;cursor.visible=false;cursor.castShadow=false;
const tools=[['food','香蕉'],['plant','植物'],['rock','岩石'],['puddle','水洼'],['stump','树桩'],['wall','石墙'],['floor','擦除'],['spawn','出生点']];
for(const [tool,label]of tools){const b=document.createElement('button');b.textContent=label;b.classList.toggle('selected',tool===selectedTool);b.onclick=()=>{selectedTool=tool;[...$('palette').children].forEach(x=>x.classList.toggle('selected',x===b));};$('palette').appendChild(b);}
$('editor').onclick=async()=>{edit=!edit;$('editpanel').hidden=!edit;$('editor').textContent=edit?'完成编辑':'✎ 编辑栖境';cursor.visible=edit;if(edit){await command({action:'pause',value:true});cameraView('overview');toast('点击地面放置；拖动仍可旋转视角');}};
for(const action of ['save','load','garden'])$(action).onclick=async()=>{try{await command({action});toast({save:'地图已保存到项目 maps 文件夹',load:'已载入保存的地图',garden:'已恢复自然栖境，原存档未覆盖'}[action]);}catch(e){toast(e.message);}};
const raycaster=new T.Raycaster(),mouse=new T.Vector2(),plane=new T.Plane(new T.Vector3(0,1,0),0),hit=new T.Vector3();let cell=null,down=null;
renderer.domElement.addEventListener('pointermove',e=>{if(!edit)return;mouse.set(e.clientX/innerWidth*2-1,-e.clientY/innerHeight*2+1);raycaster.setFromCamera(mouse,camera);if(raycaster.ray.intersectPlane(plane,hit)){cell={x:Math.floor(hit.x),y:Math.floor(hit.z)};cursor.position.set(cell.x+.5,.015,cell.y+.5);cursor.visible=cell.x>0&&cell.y>0&&cell.x<mapData.grid[0].length-1&&cell.y<mapData.grid.length-1;}});
renderer.domElement.addEventListener('pointerdown',e=>down={x:e.clientX,y:e.clientY});
renderer.domElement.addEventListener('pointerup',e=>{if(edit&&cell&&down&&Math.hypot(e.clientX-down.x,e.clientY-down.y)<5)command({action:'paint',...cell,tool:e.button===2?'floor':selectedTool}).catch(e=>toast(e.message));down=null;});
renderer.domElement.addEventListener('contextmenu',e=>e.preventDefault());
addEventListener('resize',()=>{camera.aspect=innerWidth/innerHeight;camera.updateProjectionMatrix();renderer.setSize(innerWidth,innerHeight);});
let last=performance.now();function animate(now){requestAnimationFrame(animate);const dt=Math.min((now-last)/1000,.05);last=now;
 if(latest){const target=new T.Vector3(latest.fly.x,0,latest.fly.y),previous=flyRoot.position.clone();flyRoot.position.lerp(target,1-Math.exp(-dt*14));flyRoot.rotation.y=-latest.fly.heading;
 if(follow&&!edit){const delta=flyRoot.position.clone().sub(previous);camera.position.add(delta);controls.target.add(delta);}
 const t=latest.time;
 for(const a of animated){let phase=/right/.test(a.name)?Math.PI:0;if(/T2/.test(a.name))phase+=Math.PI;let angle=0;
 if(/wing/.test(a.name))angle=Math.sin(t*25)*.025;
 else if(/head/.test(a.name))angle=latest.fly.state==='feeding'?Math.sin(t*8)*.07:0;
 else angle=Math.sin(t*15+phase)*(/coxa/.test(a.name)?.1:.15)*Math.min(latest.fly.speed,1);
 a.node.quaternion.copy(a.base).multiply(new T.Quaternion().setFromAxisAngle(new T.Vector3(0,0,1),angle));}
 sun.target.position.copy(flyRoot.position);sun.position.copy(flyRoot.position).add(new T.Vector3(-7,16,5));}
 controls.update();renderer.render(scene,camera);frameCount++;if(now-lastFps>1000){$('fps').textContent=Math.round(frameCount*1000/(now-lastFps))+' FPS';frameCount=0;lastFps=now;}
 window.cyberflyReady=!!flyModel;window.renderInfo={calls:renderer.info.render.calls,triangles:renderer.info.render.triangles};}
requestAnimationFrame(animate);
