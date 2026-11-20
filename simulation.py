import json, math, random

SPEED=6.; CAP=10; COST=10; PICKUP=1.; INTERACT=2.; PULSE_COST=3; PULSE_RADIUS=5.; INVULN=90; STUN=120; SHADE_SPEED=4.; HIT=1.; SAFE=6.; FALL_ENABLED=True
SHADE_CAP={1:6,2:8,3:10}
# Ticket-03 lantern fuel, kept in integer 1/60 units to avoid float drift (6000 = 100.0 fuel)
FUEL_MAX_U=6000; LOW_FUEL_U=1800; DRAIN_U=5; FUEL_PER_MOTE_U=600; RELIGHT_COST=5; CAP_MAX=20; WIN_RATIO=0.6
PADS={2:[((20,0,18),14.,24.,(70,0)),((50,0,-18),14.,24.,(0,0))],3:[((0,3,13),12.,8.,None)]}
DURATIONS={1:240,2:270,3:300}; DASH_SPEED=14.; DASH_TICKS=12; DASH_CD=90
LANTERNS={1:[[0,0,25],[23.8,0,7.7],[14.7,0,-20.2],[-14.7,0,-20.2],[-23.8,0,7.7]],2:[[0,0,20],[17,0,-10],[-17,0,-10],[70,0,20],[87,0,-10],[53,0,-10]],3:[[0,6,6],[18,3,10],[-18,3,10],[35,0,-10],[-35,0,-10],[20,0,-35],[-20,0,-35]]}
def dist(a,b): return math.hypot(a[0]-b[0],a[2]-b[2])
def load_json(path,default):
    if not path:return default
    with open(path,encoding='utf-8') as f:return json.load(f)
class Game:
    def __init__(self,seed=1,night=1,scenario=None):
        self.rng=random.Random(seed);self.seed=seed;self.night=night;self.tick=0;self.sim_tick=0;self.time=DURATIONS[night]*60;self.score=0;self.state='playing';self.flames=3;self.carried=0;self.player=[0.,0.,0.];self.invuln=0;self.dash_cd=0;self.pulse_cd=0;self.dash_left=0;self.pulse_push={};self.face=[0.,1.];self.vel=[0.,0.,0.];self.grounded=True;self.charm=0;self.pause=False;self.prev={x:False for x in ('jump','dash','pulse','interact','pause')};self.input={'move':[0,0],'cam_yaw_deg':0,'jump':False,'dash':False,'pulse':False,'interact':False,'pause':False};self.events=[];self.killscore=set();self.return_ticks=0;self.wind={'active':False,'dir_deg':0};self.wind_timer=0;self.launch=None;self.fall_wait=0;self.started=False;self.bench=False
        self.lanterns=[{'id':f'L{i+1}','pos':list(p),'lit':False,'deposited':0,'fu':0,'ever_lit':False,'relit_count':0} for i,p in enumerate(LANTERNS[night])];self.successful_lights=0
        self.spawn_points=self._mote_points();self.shade_points=self._shade_points();self.motes=[self._mote(f'M{i+1}',p) for i,p in enumerate(self.spawn_points[:20])];self.shades=[];self.drifters=[]
        charm_positions={1:[],2:[[35,0,0]],3:[[30,0,25],[-30,0,25]]}[night];self.charms=[{'id':f'C{i+1}','pos':p,'available':True,'respawn':0} for i,p in enumerate(charm_positions)]
        self.random_motes=True;self.random_shades=True;self.random_drifters=True;self.wind_enabled=night==3;self.shade_spawn=300;self.drifter_spawn=1200
        if scenario:self._scenario(scenario)
    def _mote_points(self):
        if self.night==1:return [[r*math.cos(math.radians(a)),0,r*math.sin(math.radians(a))] for r,angles in ((12,range(0,360,45)),(33,[i*22.5 for i in range(16)])) for a in angles]
        if self.night==2:return [[cx+r*math.cos(math.radians(a)),0,r*math.sin(math.radians(a))] for cx in (0,70) for r,angles in ((10,(0,90,180,270)),(22,range(0,360,45))) for a in angles]
        return [[34*math.cos(math.radians(a)),0,34*math.sin(math.radians(a))] for a in range(0,360,20)]+[[18*math.cos(math.radians(a)),3,18*math.sin(math.radians(a))] for a in range(20,180,20)]+[[5*math.cos(math.radians(a)),6,5*math.sin(math.radians(a))] for a in (45,135,225,315)]
    def _shade_points(self):
        if self.night==2:return [[cx+r*math.cos(math.radians(a)),0,r*math.sin(math.radians(a))] for cx in (0,70) for r,angles in ((26,range(22,360,45)),) for a in angles]
        r=43 if self.night==3 else 37;angles=[i*22.5 for i in range(16)] if self.night==3 else range(0,360,30)
        return [[r*math.cos(math.radians(a)),0,r*math.sin(math.radians(a))] for a in angles]
    def _mote(self,id,pos,kind='random',ttl=0):return {'id':id,'pos':list(pos),'kind':kind,'ttl':ttl}
    def _scenario(self,sc):
        p=sc.get('player',{});self.player=list(map(float,p.get('pos',[0,0,0])));self.carried=int(p.get('carried',0));self.flames=int(p.get('flames',3));self.invuln=int(p.get('invuln_ticks',0));self.dash_cd=int(p.get('dash_cd_ticks',0));self.pulse_cd=int(p.get('pulse_cd_ticks',0));self.charm=int(p.get('charm_ticks',0));self.successful_lights=int(p.get('successful_lights',0))
        self.random_motes=sc.get('random_motes',True);self.random_shades=sc.get('random_shades',True);self.random_drifters=sc.get('random_drifters',True);self.wind_enabled=sc.get('wind_enabled',self.wind_enabled)
        if 'motes' in sc:self.motes=[self._mote(f'M{i+1}',x) for i,x in enumerate(sc['motes'])]
        if 'shades' in sc:self.shades=[{'id':x.get('id',f'S{i+1}'),'pos':list(map(float,x['pos'])),'state':x.get('state','wander'),'state_ticks':x.get('state_ticks_left',0),'recoil':[0,0,0],'target':x.get('target_lantern_id'),'drain_t':0} for i,x in enumerate(sc['shades'])]
        if 'drifters' in sc:self.drifters=[{'id':x.get('id',f'D{i+1}'),'pos':list(map(float,x['pos'])),'state':x.get('state','idle'),'stolen':x.get('stolen',0),'ticks':0} for i,x in enumerate(sc['drifters'])]
        if 'charms' in sc:self.charms=[{'id':x.get('id',f'C{i+1}'),'pos':list(map(float,x.get('pos',[0,0,0]))),'available':x.get('available',True),'respawn':x.get('respawn_ticks',0)} for i,x in enumerate(sc['charms'])]
        for x in sc.get('lanterns',[]):
            l=next((a for a in self.lanterns if a['id']==x.get('id')),None)
            if l:
                l['pos']=list(x.get('pos',l['pos']));l['lit']=bool(x.get('lit',False));l['deposited']=x.get('deposited',COST if l['lit'] else 0)
                l['fu']=int(round(float(x.get('fuel',100 if l['lit'] else 0))*60)) if l['lit'] else 0
                l['ever_lit']=bool(x.get('ever_lit',l['lit']))
        self.time=int(sc.get('time_left_s',DURATIONS[self.night])*60)
    def event(self,name,data):self.events.append({'type':'event','tick':self.tick,'name':name,'data':data})
    def spawn_shades(self,count):
        free=[p for p in self.shade_points if dist(p,self.player)>=15 and not any(dist(p,s['pos'])<3 for s in self.shades)]
        for _ in range(min(count,SHADE_CAP[self.night]-len(self.shades),len(free))):
            pos=free.pop(0); sid=f'S{len(self.shades)+1}';self.shades.append({'id':sid,'pos':pos[:],'state':'spawning','state_ticks':30,'recoil':[0,0,0]});self.event('shade_spawned',{'id':sid})
    def step(self):
        if self.state not in ('playing','paused'):return
        k=self.tick;self.tick+=1
        pause_pressed=self.input.get('pause',False) and not self.prev['pause'];self.prev['pause']=self.input.get('pause',False)
        if pause_pressed:self.state='playing' if self.state=='paused' else 'paused';self.event('resumed' if self.state=='playing' else 'paused',{})
        if self.state=='paused':return
        self.sim_tick+=1;self.time-=1
        self.invuln=max(0,self.invuln-1);self.dash_cd=max(0,self.dash_cd-1);self.pulse_cd=max(0,self.pulse_cd-1);self.charm=max(0,self.charm-1)
        for s in self.shades:
            if s['state_ticks']>0:s['state_ticks']-=1
            if s['state']=='stunned' and s['state_ticks']==0:s['state']='wander'
            if s['state']=='spawning' and s['state_ticks']==0:s['state']='wander'
        if not self.bench:self._fuel_tick()
        for m in self.motes[:]:
            if m['ttl']>0:m['ttl']-=1
            if m['ttl']==0 and m['kind']=='dropped':self.motes.remove(m)
        if not self.started:self.started=True;self.event('night_start',{'night':self.night})
        if self.fall_wait>0:
            # Ticket-02: after a fall wait 60 ticks (no pickup, no hits), then respawn at the start point.
            self.fall_wait-=1
            if self.fall_wait==0:self.player=[0.,0.,0.];self.vel=[0.,0.,0.];self.grounded=True;self.launch=None;self.face=[0.,1.];self.invuln=INVULN
            self._world_only();return
        self._move_player()
        if FALL_ENABLED and self.player[1]<-10:
            self.flames-=1;lost=self.carried;self.carried=0;self.event('player_hit',{'by':'fall','flames':self.flames,'dropped':0,'lost':lost})
            if self.flames<=0:self.finish('lost','no_flames');return
            self.fall_wait=60;self.vel=[0.,0.,0.];self.dash_left=0;self.launch=None
            self._world_only();return
        self._pickup();self._interact();self._safe_zones();self._pulse();self._pulse_push();self._move_enemies();self._collisions();self._spawns();self._win_check()
        for name in ('jump','dash','pulse','interact'): self.prev[name]=self.input.get(name,False)
    def _lantern(self,lid):return next((l for l in self.lanterns if l['id']==lid),None)
    def capacity(self):return min(CAP_MAX,CAP+2*self.successful_lights)
    def _fuel_tick(self):
        drain={}
        for s in self.shades:
            if s['state']=='drain' and s.get('target'):drain[s['target']]=drain.get(s['target'],0)+DRAIN_U
        for l in self.lanterns:
            if not l['lit']:continue
            l['fu']-=1+drain.get(l['id'],0)
            if l['fu']<=0:l['fu']=0;l['lit']=False;l['deposited']=0;self.event('lantern_out',{'lantern_id':l['id']})
        for s in sorted(self.shades,key=lambda a:int(a['id'][1:])):
            if s['state']!='drain':continue
            l=self._lantern(s.get('target'))
            if not l or not l['lit']:continue
            s['drain_t']=s.get('drain_t',0)+1
            if s['drain_t']%60==0:self.event('fuel_drain',{'lantern_id':l['id'],'shade_id':s['id'],'fuel':round(l['fu']/60,1)})
    def _world_only(self):
        self._safe_zones();self._pulse_push();self._move_enemies();self._spawns();self._win_check()
        for name in ('jump','dash','pulse','interact'): self.prev[name]=self.input.get(name,False)
    def _move_player(self):
        x,z=self.input.get('move',[0,0]);mag=math.hypot(x,z)
        if mag>1:x,z=x/mag,z/mag
        th=math.radians(self.input.get('cam_yaw_deg',0));dx=x*math.cos(th)+z*math.sin(th);dz=-x*math.sin(th)+z*math.cos(th)
        if math.hypot(dx,dz)>.01:self.face=[dx,dz]
        if self._pressed('jump') and self.grounded:self.vel[1]=7;self.grounded=False
        if self._pressed('dash') and self.dash_cd==0 and self.dash_left==0:
            self.dash_left=12;self.dash_cd=0 if self.charm else DASH_CD;self.event('dash',{})
        dashing=self.dash_left>0
        if dashing:self.vel[0]=self.face[0]*DASH_SPEED;self.vel[2]=self.face[1]*DASH_SPEED;self.dash_left-=1
        elif self.launch is not None:self.vel[0],self.vel[2]=self.launch
        else:self.vel[0]=dx*(7.2 if self.charm else SPEED);self.vel[2]=dz*(7.2 if self.charm else SPEED)
        ox,oz=self.player[0],self.player[2]
        self.player[0]+=self.vel[0]/60;self.player[2]+=self.vel[2]/60
        # vertical cliffs: cannot move into ground higher than the feet (ramps rise gently enough to pass)
        surf=self._surface(self.player[0],self.player[2])
        inside_tower=self.night==3 and math.hypot(ox,oz)<=2  # the standard start (0,0,0) sits in the bell tower footprint
        if surf is not None and surf-self.player[1]>0.35 and not inside_tower:self.player[0],self.player[2]=ox,oz
        surf=self._ground(self.player[0],self.player[2])
        if self.grounded and (surf is None or self.player[1]>surf+0.35):self.grounded=False;self.vel[1]=0
        elif self.grounded and surf is not None:self.player[1]=surf
        if not self.grounded and not dashing:self.vel[1]-=20/60;self.player[1]+=self.vel[1]/60
        surf=self._ground(self.player[0],self.player[2])
        if not self.grounded and surf is not None and self.vel[1]<=0 and self.player[1]<=surf and surf-self.player[1]<=0.6:
            self.player[1]=surf;self.vel[1]=0;self.grounded=True;self.launch=None
        if self.grounded:
            for (px,py,pz),vy,vh,target in PADS.get(self.night,[]):
                if math.hypot(self.player[0]-px,self.player[2]-pz)<=1 and abs(self.player[1]-py)<=0.5:
                    if target is None:hx,hz=0.,-1.
                    else:
                        hx,hz=target[0]-px,target[1]-pz;n=math.hypot(hx,hz);hx,hz=hx/n,hz/n
                    self.launch=[hx*vh,hz*vh];self.vel=[hx*vh,vy,hz*vh];self.grounded=False;break
        if self.night==3 and self.wind_enabled:
            # Ticket-02: a 5 s gust every 30 s, direction chosen 2 s before it starts
            self.wind_timer=(self.wind_timer+1)%1800;active=self.wind_timer>=1500;self.wind={'active':active,'dir_deg':self.wind.get('dir_deg',0)}
            if self.wind_timer==1380:self.wind['dir_deg']=self.rng.randrange(360)
            if active:self.player[0]+=math.cos(math.radians(self.wind['dir_deg']))*2/60;self.player[2]+=math.sin(math.radians(self.wind['dir_deg']))*2/60
    def _ground(self,x,z):
        # Assumption (Ticket-02 gives Night 3 no separate start): a player below the tower top stands on tier 2
        # inside the tower footprint, so the (0,0,0) start lands on Y=6 and can walk out; from outside the tower stays solid.
        s=self._surface(x,z)
        return 6. if s==14. and self.player[1]<13 else s
    def _surface(self,x,z):
        if self.night==1:return 0 if math.hypot(x,z)<=40 else None
        if self.night==2:return 0 if math.hypot(x,z)<=28 or math.hypot(x-70,z)<=28 or (26<=x<=44 and abs(z)<=2) else None
        r=math.hypot(x,z)
        if r<=2:return 14.  # bell tower: solid, cannot be climbed
        if r<=8:return 6
        if 12<=r<=24 and z>0:return 3
        if r>45:return None
        h=0.
        for a in (math.radians(30),math.radians(150)):
            along=x*math.cos(a)+z*math.sin(a);perp=-x*math.sin(a)+z*math.cos(a)
            if abs(perp)<=1.5 and 24<=along<=30:h=max(h,(30-along)/6*3)
        return h
    def _pressed(self,key):return self.input.get(key,False) and not self.prev[key]
    def _pickup(self):
        if self.bench:return
        for m in self.motes[:]:
            if self.carried<self.capacity() and dist(m['pos'],self.player)<=PICKUP and abs(m['pos'][1]-self.player[1])<=1.5:
                self.motes.remove(m);self.carried+=1;self.event('mote_picked',{'carried':self.carried})
        for c in self.charms:
            if c['available'] and dist(c['pos'],self.player)<=PICKUP and abs(c['pos'][1]-self.player[1])<=1.5:c['available']=False;c['respawn']=2700;self.charm=600;self.event('charm_picked',{'charm_id':c['id'],'charm_ticks':600})
    def _interact(self):
        if not self._pressed('interact') or not self.carried:return
        # candidates: unlit lanterns, or lit ones that are not full; nearest first, then lower id
        cands=[(dist(l['pos'],self.player),int(l['id'][1:]),l) for l in self.lanterns
               if dist(l['pos'],self.player)<=INTERACT and (not l['lit'] or l['fu']<FUEL_MAX_U)]
        if not cands:return
        l=min(cands,key=lambda c:(c[0],c[1]))[2]
        if l['lit']:
            used=min(self.carried,-(-(FUEL_MAX_U-l['fu'])//FUEL_PER_MOTE_U))
            if used<=0:return
            self.carried-=used;l['fu']=min(FUEL_MAX_U,l['fu']+FUEL_PER_MOTE_U*used);self.score+=5*used
            self.event('refuel',{'lantern_id':l['id'],'amount':used,'fuel':round(l['fu']/60,1)})
            return
        cost=RELIGHT_COST if l['ever_lit'] else COST
        n=min(self.carried,cost-l['deposited']);self.carried-=n;l['deposited']+=n;self.score+=5*n
        self.event('deposit',{'lantern_id':l['id'],'amount':n,'deposited':l['deposited']})
        if l['deposited']>=cost:
            relight=l['ever_lit'];l['lit']=True;l['fu']=FUEL_MAX_U;l['ever_lit']=True;self.successful_lights+=1
            if relight:l['relit_count']+=1;self.score+=40
            else:self.score+=100
            self.event('lantern_lit',{'lantern_id':l['id'],'relight':relight})
    def _safe_zones(self):
        for s in self.shades:
            if s['state'] in ('stunned','spawning'):continue
            for l in self.lanterns:
                d=dist(s['pos'],l['pos'])
                if l['lit'] and l['fu']>=LOW_FUEL_U and d<SAFE:
                    dx=s['pos'][0]-l['pos'][0];dz=s['pos'][2]-l['pos'][2];d=d or 1;s['pos'][0]=l['pos'][0]+dx/d*SAFE;s['pos'][2]=l['pos'][2]+dz/d*SAFE
    def _pulse(self):
        if self._pressed('pulse') and self.carried>=3 and self.pulse_cd==0:
            self.carried-=3;self.pulse_cd=180;ids=[]
            for s in sorted(self.shades,key=lambda a:a['id']):
                if math.dist(self.player,[s['pos'][0],s['pos'][1]-.8,s['pos'][2]])<=PULSE_RADIUS:
                    self.score+=15 if s['state']=='drain' else 5
                    s['state']='stunned';s['state_ticks']=STUN;s['drain_t']=0;ids.append(s['id'])
                    dx=s['pos'][0]-self.player[0];dz=s['pos'][2]-self.player[2];d=math.hypot(dx,dz)
                    if d<1e-9:dx,dz,d=1.,0.,1.
                    self.pulse_push[s['id']]=[dx/d*4/15,dz/d*4/15,15]
            for d in self.drifters:
                if dist(d['pos'],self.player)<=PULSE_RADIUS and d['state']=='chase':d['state']='flee';d['ticks']=240
                elif dist(d['pos'],self.player)<=PULSE_RADIUS and d['state']=='flee' and d['stolen']:
                    self.motes.extend(self._mote(f'R{self.sim_tick}-{i}',d['pos'],'dropped',480) for i in range(d['stolen']));self.event('drifter_drop',{'drifter_id':d['id'],'amount':d['stolen']});d['stolen']=0;d['state']='removed';d['ticks']=120
            self.event('pulse',{'stunned_ids':ids})
    def _pulse_push(self):
        for s in self.shades:
            p=self.pulse_push.get(s['id'])
            if p and p[2]>0 and s['state']=='stunned':s['pos'][0]+=p[0];s['pos'][2]+=p[1];p[2]-=1
    def _move_enemies(self):
        for s in self.shades:
            if s['state'] in ('stunned','spawning'):continue
            speed=4.5 if self.night==3 else SHADE_SPEED
            dx=self.player[0]-s['pos'][0];dz=self.player[2]-s['pos'][2];d=math.hypot(dx,dz)
            if self.bench:d=1e9
            if s['state']=='recoil':
                s['pos'][0]+=s['recoil'][0]/60;s['pos'][2]+=s['recoil'][2]/60;s['state_ticks']-=1
                if s['state_ticks']<=0:s['state']='chase'
                continue
            if s['state']=='drain':
                l=self._lantern(s.get('target'))
                if d<=6:s['state']='chase'
                elif not l or not l['lit'] or l['fu']>=LOW_FUEL_U or dist(s['pos'],l['pos'])>2:s['state']='wander';s['drain_t']=0;continue
                else:continue  # standing still, draining
            if s['state']=='chase' and d>18:s['state']='wander'
            if s['state']=='wander' and d<=12:s['state']='chase'
            if s['state']=='chase':
                if d:s['pos'][0]+=dx/d*speed/60;s['pos'][2]+=dz/d*speed/60
                continue
            # wander: go to the nearest weak lit lantern (fuel < 30), else the nearest unlit lantern
            weak=[(dist(s['pos'],l['pos']),int(l['id'][1:]),l) for l in self.lanterns if l['lit'] and l['fu']<LOW_FUEL_U]
            if weak:
                td,_,tl=min(weak,key=lambda c:(c[0],c[1]));s['target']=tl['id']
                if td<=2:s['state']='drain';s['drain_t']=0;continue
            else:
                dark=[(dist(s['pos'],l['pos']),int(l['id'][1:]),l) for l in self.lanterns if not l['lit']]
                if not dark:continue
                td,_,tl=min(dark,key=lambda c:(c[0],c[1]))
                if td<=2:continue
            tx=tl['pos'][0]-s['pos'][0];tz=tl['pos'][2]-s['pos'][2];n=math.hypot(tx,tz)
            if n:step=min(speed/60,n);s['pos'][0]+=tx/n*step;s['pos'][2]+=tz/n*step
        for d in self.drifters:
            if d['state']=='removed':d['ticks']-=1;continue
            near=dist(d['pos'],self.player)
            if d['state']=='idle':
                if near<=15 and self.carried>=5:d['state']='chase'
                else:d['pos'][0]+=math.sin(self.sim_tick/30)*2/60
            if d['state']=='chase' and (self.carried<5 or near>15):d['state']='idle'
            if d['state']=='chase' and near:d['pos'][0]+=(self.player[0]-d['pos'][0])/near*7/60;d['pos'][2]+=(self.player[2]-d['pos'][2])/near*7/60
            if d['state']=='flee':
                d['ticks']-=1
                if near:d['pos'][0]+=(d['pos'][0]-self.player[0])/near*7/60;d['pos'][2]+=(d['pos'][2]-self.player[2])/near*7/60
                if d['ticks']<=0:d['state']='removed'
    def _collisions(self):
        if self.bench:return
        for d in self.drifters:
            if d['state']=='chase' and dist(d['pos'],self.player)<=1.2:
                amount=min(3,self.carried);self.carried-=amount;d['stolen']=amount;d['state']='flee';d['ticks']=240;self.event('drifter_steal',{'drifter_id':d['id'],'amount':amount,'carried':self.carried})
        if self.return_ticks>0:self.return_ticks-=1;return
        if self.invuln:return
        for s in sorted(self.shades,key=lambda a:a['id']):
            if s['state'] in ('stunned','spawning'):continue
            if dist(s['pos'],self.player)<=HIT and abs(s['pos'][1]-self.player[1])<=1.5:
                self.flames-=1;dropped=self.carried//2;self.carried-=dropped;self.invuln=90;s['state']='recoil';s['state_ticks']=60;dx=s['pos'][0]-self.player[0];dz=s['pos'][2]-self.player[2];d=math.hypot(dx,dz) or 1;s['recoil']=[dx/d*2,dz/d*2,0]
                for i in range(dropped):a=self.rng.random()*math.tau;r=self.rng.uniform(1.5,2.5);self.motes.append(self._mote(f'R{self.sim_tick}-{i}',[self.player[0]+math.cos(a)*r,self.player[1],self.player[2]+math.sin(a)*r],'dropped',480))
                self.event('player_hit',{'by':'shade','flames':self.flames,'dropped':dropped})
                if self.flames<=0:self.finish('lost','no_flames')
                break
    def _spawns(self):
        if self.bench:return
        if self.sim_tick%240==0 and len(self.motes)<30:
            free=[p for p in self.spawn_points if not any(dist(p,m['pos'])<1 for m in self.motes)]
            if free:self.motes.append(self._mote(f'R{self.sim_tick}',self.rng.choice(free)))
        interval={1:480,2:420,3:360}[self.night]
        if self.sim_tick>=300 and (self.sim_tick-300)%interval==0 and len(self.shades)<({1:6,2:8,3:10}[self.night]):self.spawn_shades(2 if self.sim_tick==300 else 1)
        if self.night in (2,3) and self.sim_tick%1200==0 and len([d for d in self.drifters if d['state']!='removed'])<2:
            ident=f'D{sum(1 for d in self.drifters)+1}';pos=self._free_point();self.drifters.append({'id':ident,'pos':pos,'state':'idle','stolen':0,'ticks':0});self.event('drifter_spawned',{'id':ident})
        for c in self.charms:
            if not c['available'] and c['respawn']>0:c['respawn']-=1
            if not c['available'] and c['respawn']==0:c['available']=True
    def _free_point(self):
        candidates=self.shade_points
        return self.rng.choice(candidates) if candidates else [0,0,0]
    def _win_check(self):
        if self.bench:return
        if self.flames<=0:self.finish('lost','no_flames')
        elif self.time<=0:
            lit=sum(1 for l in self.lanterns if l['lit'])
            if lit>=math.ceil(WIN_RATIO*len(self.lanterns)):self.finish('won','dawn_survived')
            else:self.finish('lost','dawn')
    def finish(self,state,reason):
        if self.state!='playing':return
        self.state=state
        if state=='won':self.score+=sum(50+l['fu']//60 for l in self.lanterns if l['lit'])+50*self.flames
        self.event('game_over',{'result':state,'reason':reason})
    def snapshot(self):
        return {'type':'snapshot','tick':self.tick,'sim_tick':self.sim_tick,'night':self.night,'state':self.state,'time_left_s':round(self.time/60,3),'score':self.score,'wind':self.wind,'player':{'pos':[round(v,3) for v in self.player],'vel':[round(v,3) for v in self.vel],'grounded':self.grounded,'flames':self.flames,'carried':self.carried,'invuln':self.invuln/60,'dash_cd_s':self.dash_cd/60,'pulse_cd_s':self.pulse_cd/60,'charm_s':self.charm/60,'capacity':self.capacity()},'lanterns':[{'id':l['id'],'pos':l['pos'],'lit':l['lit'],'deposited':l['deposited'],'fuel':round(l['fu']/60,1) if l['lit'] else 0,'ever_lit':l['ever_lit'],'relit_count':l['relit_count']} for l in self.lanterns],'shades':[{'id':s['id'],'pos':[round(v,3) for v in s['pos']],'state':s['state']} for s in self.shades],'motes':[{'id':m['id'],'pos':[round(v,3) for v in m['pos']],'kind':m['kind'],'ttl_s':round(m['ttl']/60,3)} for m in self.motes],'motes_active':len(self.motes),'drifters':[{'id':d['id'],'pos':[round(v,3) for v in d['pos']],'state':d['state'],'stolen':d['stolen']} for d in self.drifters if d['state']!='removed'],'charms':[{'id':c['id'],'available':c['available'],'respawn_s':c['respawn']/60} for c in self.charms]}
def bench_game(seed=42):
    """Ticket-04 standard bench scene: Night 1, 200 wander shades and 100 motes spread with the seed, L1-L3 lit at fuel 100."""
    g=Game(seed,1);g.bench=True;rng=random.Random(seed)
    def spot(rmax):
        r=rmax*math.sqrt(rng.random());a=rng.random()*math.tau;return [r*math.cos(a),0.,r*math.sin(a)]
    g.shades=[{'id':f'S{i+1}','pos':spot(38),'state':'wander','state_ticks':0,'recoil':[0,0,0],'target':None,'drain_t':0} for i in range(200)]
    g.motes=[g._mote(f'M{i+1}',spot(38)) for i in range(100)]
    for l in g.lanterns[:3]:l['lit']=True;l['fu']=FUEL_MAX_U;l['ever_lit']=True;l['deposited']=COST
    return g
def run_headless(seed,ticks,every,scenario_path=None,inputs_path=None,night=1):
    sc=load_json(scenario_path,{})
    if not isinstance(sc,dict):raise ValueError('scenario must be an object')
    data=load_json(inputs_path,{'frames':[]});frames=data.get('frames',[])
    if not isinstance(frames,list):raise ValueError('inputs.frames must be an array')
    last=-1
    for f in frames:
        if not isinstance(f,dict) or not isinstance(f.get('tick'),int) or f['tick']<=last:raise ValueError('frame ticks must strictly increase')
        last=f['tick']
        if 'move' in f and (not isinstance(f['move'],list) or len(f['move'])!=2 or any(not isinstance(v,(int,float)) or abs(v)>1 for v in f['move'])):raise ValueError('move must contain two values in [-1,1]')
        for key in ('jump','dash','interact','pulse','pause'):
            if key in f and not isinstance(f[key],bool):raise ValueError(f'{key} must be boolean')
    if night not in (1,2,3):raise ValueError('night must be 1, 2, or 3')
    g=Game(seed,night,sc);out=[json.dumps(g.snapshot(),separators=(',',':'))];idx=0
    for k in range(ticks):
        while idx<len(frames) and frames[idx]['tick']==k:g.input.update(frames[idx]);idx+=1
        g.step();out.extend(json.dumps(e,separators=(',',':')) for e in g.events);g.events.clear()
        if g.tick%every==0:out.append(json.dumps(g.snapshot(),separators=(',',':')))
        if g.state in ('won','lost'):break
    out.append(json.dumps({'type':'end','ticks':g.tick,'sim_tick':g.sim_tick,'state':g.state,'score':g.score},separators=(',',':')));return out
