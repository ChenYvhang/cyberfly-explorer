/* Browser-only controller for the public demo. The local application never
   loads this file and continues to use the Python MaleCNS backend. */
(() => {
  const nativeFetch=window.fetch.bind(window),width=24,height=20,dt=.02,clamp=(v,a,b)=>Math.max(a,Math.min(b,v)),wrap=a=>(a+Math.PI)%(Math.PI*2)-Math.PI;
  const garden=()=>({
    grid:Array.from({length:height},(_,y)=>Array.from({length:width},(_,x)=>x===0||y===0||x===width-1||y===height-1?'#':'.')),
    foods:[[14,10],[7,6],[18,15],[4,15]].map(([x,y])=>({x,y,radius:.28})),
    decor:[...[ [8,8,1.6],[15,7,1.8],[17,12,1.4],[6,12,1.7],[12,14,1.5],[4,5,1.8] ].map(([x,y,height])=>({kind:'plant',x,y,radius:.32,height,solid:true})),
      ...[[9,11,.55,.65],[16,9,.7,.85],[5,8,.6,.5],[14,15,.4,.55]].map(([x,y,radius,height])=>({kind:'rock',x,y,radius,height,solid:true})),
      {kind:'stump',x:19,y:6,radius:.55,height:1,solid:true},{kind:'puddle',x:11,y:6,radius:1.2,height:.01,solid:false}]
  });
  let grid,foods,decor,fly,time,distance,trail,revision=0,paused=true;
  function reset(){({grid,foods,decor}=garden());fly={x:11.5,y:9.5,heading:.25,speed:0,energy:1,foods_found:0,state:'exploring',feeding_time:0};time=distance=0;trail=[];paused=true;revision++}
  function wall(x,y){let ix=Math.floor(x),iy=Math.floor(y);return !grid[iy]||grid[iy][ix]==='#'||decor.some(o=>o.solid&&Math.hypot(x-o.x,y-o.y)<o.radius+.16)}
  function nearestFood(){return foods.slice().sort((a,b)=>Math.hypot(fly.x-a.x,fly.y-a.y)-Math.hypot(fly.x-b.x,fly.y-b.y))[0]}
  function tick(){if(paused)return;let food=nearestFood(),dist=food?Math.hypot(food.x-fly.x,food.y-fly.y):99,bearing=food?wrap(Math.atan2(food.y-fly.y,food.x-fly.x)-fly.heading):0;
    let ahead=wall(fly.x+Math.cos(fly.heading)*.55,fly.y+Math.sin(fly.heading)*.55),turn=ahead?1.0:clamp(bearing*.85,-.72,.72),forward=dist<.48?.04:.72;
    fly.state=dist<.48?'feeding':ahead?'avoiding':dist<5?'tracking food':'exploring';fly.feeding_time=fly.state==='feeding'?fly.feeding_time+dt:0;fly.heading=wrap(fly.heading+turn*2.2*dt);fly.speed+=(forward-fly.speed)*dt*5;
    let nx=fly.x+Math.cos(fly.heading)*fly.speed*dt,ny=fly.y+Math.sin(fly.heading)*fly.speed*dt;if(!wall(nx,ny)){fly.x=nx;fly.y=ny;distance+=fly.speed*dt}else fly.heading=wrap(fly.heading+.65);
    time+=dt;fly.energy=Math.max(0,fly.energy-fly.speed*dt*.002);if(fly.feeding_time>1&&food){foods=foods.filter(f=>f!==food);fly.foods_found++;fly.feeding_time=0;fly.energy=Math.min(1,fly.energy+.3);revision++}
    if(!trail.length||Math.hypot(fly.x-trail.at(-1)[0],fly.y-trail.at(-1)[1])>.06)trail.push([fly.x,fly.y]);trail=trail.slice(-400);
  }
  function state(){let food=nearestFood(),bearing=food?wrap(Math.atan2(food.y-fly.y,food.x-fly.x)-fly.heading):0;return {fly,stats:{motor_forward:.72,motor_turn:clamp(bearing*.85,-.72,.72),motor_escape:0,steer_L:Math.max(0,-bearing)*13,steer_R:Math.max(0,bearing)*13,active:1842,step_ms:.25},status:'demo',error:'',paused,time,revision,foods,distance,trail}}
  function world(){return {grid:grid.map(r=>r.join('')),decor,foods,revision}}
  function paint(x,y,tool){if(x<1||y<1||x>=width-1||y>=height-1)return;foods=foods.filter(o=>Math.floor(o.x)!==x||Math.floor(o.y)!==y);decor=decor.filter(o=>Math.floor(o.x)!==x||Math.floor(o.y)!==y);grid[y][x]=tool==='wall'?'#':'.';let cx=x+.5,cy=y+.5,spec={rock:[.34,.48,true],plant:[.27,.76,true],stump:[.34,.62,true],puddle:[.65,.01,false]}[tool];if(spec)decor.push({kind:tool,x:cx,y:cy,radius:spec[0],height:spec[1],solid:spec[2]});else if(tool==='food')foods.push({x:cx,y:cy,radius:.28});else if(tool==='spawn'){fly.x=cx;fly.y=cy;trail=[]}revision++}
  function command(d){if(d.action==='pause')paused=!!d.value;else if(d.action==='garden')reset();else if(d.action==='paint')paint(+d.x,+d.y,d.tool);else if(d.action==='save')localStorage.setItem('cyberfly-map',JSON.stringify({grid,foods,decor,fly}));else if(d.action==='load'){let saved=JSON.parse(localStorage.getItem('cyberfly-map')||'null');if(saved){({grid,foods,decor,fly}=saved);trail=[];revision++}}return {ok:true}}
  reset();setInterval(tick,dt*1000);const reply=(d,s=200)=>Promise.resolve(new Response(JSON.stringify(d),{status:s,headers:{'Content-Type':'application/json'}}));
  window.fetch=(input,init={})=>{let url=new URL(typeof input==='string'?input:input.url,location.href);if(!url.pathname.includes('/api/'))return nativeFetch(input,init);if(url.pathname.endsWith('/api/state'))return reply(state());if(url.pathname.endsWith('/api/world'))return reply(world());if(url.pathname.endsWith('/api/command'))return reply(command(JSON.parse(init.body||'{}')));return reply({error:'unknown demo endpoint'},404)};
  addEventListener('DOMContentLoaded',()=>{let c=document.querySelector('aside .caption');if(c)c.textContent='在线轻量演示 · FlyBody 解剖网格 · 完整 MaleCNS 版请本地运行'});
})();
