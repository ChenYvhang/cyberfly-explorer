"""Local 3D frontend + authoritative fixed-step CPU simulation."""
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from pathlib import Path
from dataclasses import asdict
import argparse
import json
import threading
import time
import mimetypes
import webbrowser
from cyberfly.world import World

ROOT = Path(__file__).resolve().parent
mimetypes.add_type('text/javascript', '.js')

class Simulation:
    def __init__(self, brain_enabled):
        self.world = World()
        self.map_path = ROOT / 'maps' / 'custom_map.json'
        if self.map_path.exists(): self.world.load(self.map_path)
        else: self.garden()
        self.lock = threading.RLock()
        self.paused = True
        self.status = 'warming' if brain_enabled else 'preview'
        self.stats = {}
        self.revision = 0
        self.error = ''
        self.brain_enabled = brain_enabled
        self.reset_requested = False
        threading.Thread(target=self.run, daemon=True).start()

    def garden(self):
        # Open experimental habitat; perimeter remains a physical barrier.
        self.world.grid = [['#' if x in (0,23) or y in (0,19) else '.' for x in range(24)] for y in range(20)]
        self.world.fly.x, self.world.fly.y = 11.5, 9.5
        self.world.fly.heading = .25
        from cyberfly.world import Food, Decor
        self.world.foods = [Food(14,10), Food(7,6), Food(18,15), Food(4,15)]
        self.world.decor = [Decor('plant',x,y,.32,h) for x,y,h in [(8,8,1.6),(15,7,1.8),(17,12,1.4),(6,12,1.7),(12,14,1.5),(4,5,1.8)]]
        self.world.decor += [Decor('rock',x,y,r,h) for x,y,r,h in [(9,11,.55,.65),(16,9,.7,.85),(5,8,.6,.5),(14,15,.4,.55)]]
        self.world.decor += [Decor('stump',19,6,.55,1),Decor('puddle',11,6,1.2,.01,False)]
        self.world.trail.clear()

    def run(self):
        try:
            if self.brain_enabled:
                from cyberfly.brain import BrainController
                brain = BrainController(ROOT / 'data' / 'male-cns')
                brain.step(self.world.senses())
                self.status = 'ready'
            while True:
                start = time.perf_counter()
                with self.lock:
                    if self.reset_requested:
                        if self.brain_enabled: brain.reset()
                        self.reset_requested = False
                    paused = self.paused
                    if not paused:
                        sense = self.world.senses()
                        if self.brain_enabled:
                            self.stats = brain.step(sense)
                            self.stats['step_ms'] = brain.step_ms
                        else:
                            self.stats = {'motor_forward': .5, 'motor_turn': .2,
                                          'motor_escape': 0, 'active': 0, 'step_ms': 0}
                        self.world.step(self.stats['motor_forward'], self.stats['motor_turn'], self.stats['motor_escape'], .02)
                time.sleep(max(.001, .02 - (time.perf_counter() - start)))
        except Exception as exc:
            self.error = str(exc); self.status = 'error'

    def snapshot(self):
        with self.lock:
            return {'fly': asdict(self.world.fly), 'stats': self.stats, 'status': self.status,
                    'error': self.error, 'paused': self.paused, 'time': self.world.time,
                    'revision': self.revision, 'foods': [asdict(f) for f in self.world.foods],
                    'distance': self.world.distance, 'trail': self.world.trail[-400:]}

    def map(self):
        with self.lock:
            return {'grid': [''.join(r) for r in self.world.grid], 'decor': [asdict(o) for o in self.world.decor],
                    'foods': [asdict(f) for f in self.world.foods], 'revision': self.revision}

    def command(self, d):
        with self.lock:
            action = d.get('action')
            if action == 'pause': self.paused = bool(d.get('value', True))
            elif action == 'paint':
                if d.get('tool') not in ['wall','floor','rock','plant','stump','puddle','food','spawn']: raise ValueError('unknown tool')
                if not self.paused: raise ValueError('Pause to edit')
                self.world.paint(int(d['x']),int(d['y']),d['tool']); self.revision += 1
            elif action == 'save': self.world.save(self.map_path)
            elif action == 'load':
                self.world.load(self.map_path); self.reset_requested = True; self.revision += 1
            elif action == 'garden':
                self.world.reset(); self.garden(); self.paused=True; self.revision+=1; self.reset_requested=True
            else: raise ValueError('unknown action')
        return {'ok': True}

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--preview',action='store_true')
    parser.add_argument('--no-browser',action='store_true')
    parser.add_argument('--port',type=int,default=8765)
    args=parser.parse_args()
    sim=Simulation(not args.preview)
    class Handler(SimpleHTTPRequestHandler):
        def __init__(self,*a,**kw): super().__init__(*a,directory=str(ROOT),**kw)
        def log_message(self,*a): pass
        def send_json(self,data,status=200):
            payload=json.dumps(data).encode()
            self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(payload))); self.end_headers(); self.wfile.write(payload)
        def do_GET(self):
            path=self.path.split('?')[0]
            if path=='/api/state': return self.send_json(sim.snapshot())
            if path=='/api/world': return self.send_json(sim.map())
            if path=='/': self.path='/web/index.html'
            elif not path.startswith(('/web/','/assets/','/node_modules/three/')) or '..' in path or '%' in path:
                return self.send_error(404)
            return super().do_GET()
        def do_POST(self):
            if self.path!='/api/command': return self.send_error(404)
            origin=self.headers.get('Origin')
            if origin and origin not in (f'http://127.0.0.1:{args.port}',f'http://localhost:{args.port}'):
                return self.send_error(403)
            try:
                n=int(self.headers.get('Content-Length','0'))
                if n>10000: raise ValueError('request too large')
                return self.send_json(sim.command(json.loads(self.rfile.read(n))))
            except Exception as exc: return self.send_json({'error':str(exc)},400)
    server=ThreadingHTTPServer(('127.0.0.1',args.port),Handler)
    print(f'Cyberfly 3D: http://127.0.0.1:{args.port}',flush=True)
    if not args.no_browser: webbrowser.open(f'http://127.0.0.1:{args.port}')
    server.serve_forever()

if __name__=='__main__': main()
