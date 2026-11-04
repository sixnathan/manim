"""Self-contained vector-like animation renderer. All generated files stay here.

Run: .venv/bin/python render.py [--stills | --audio | --render]
"""
import os
from pathlib import Path
ROOT = Path(__file__).resolve().parent
os.environ['MPLCONFIGDIR'] = str(ROOT / '.cache/matplotlib')
os.environ['XDG_CACHE_HOME'] = str(ROOT / '.cache')
os.environ['TMPDIR'] = str(ROOT / '.cache')
import asyncio, io, math, re, subprocess, sys, textwrap, json
from functools import lru_cache
import numpy as np
from PIL import Image, ImageDraw, ImageFont
import matplotlib
matplotlib.use('Agg')
from matplotlib import mathtext, font_manager
import imageio_ffmpeg
from lesson import SCENES

W,H,FPS=1280,720,24
BG='#101722'; WHITE='#e9eff6'; MUTED='#98a9ba'; BLUE='#62c4ff'; TEAL='#58dec7'; GOLD='#ffdc80'; RED='#fa8c9b'; GRID='#2a3c50'
OUT=ROOT/'output'; AUDIO=ROOT/'assets/audio'; OUT.mkdir(exist_ok=True,parents=True); AUDIO.mkdir(exist_ok=True,parents=True)
FONTDIR=Path(matplotlib.get_data_path())/'fonts/ttf'
@lru_cache(maxsize=48)
def font(n,bold=False): return ImageFont.truetype(str(FONTDIR/('DejaVuSans-Bold.ttf' if bold else 'DejaVuSans.ttf')),n)
F={n:font(n) for n in [16,18,20,22,24,26,28,32,38,46,52]}
FF=imageio_ffmpeg.get_ffmpeg_exe()
def lerp(a,b,t): return a+(b-a)*t
def ease(t): return (1-math.cos(math.pi*max(0,min(1,t))))/2
def rgba(c,a=255): return tuple(bytes.fromhex(c.lstrip('#')))+(a,)

def equation(s):
    buf=io.BytesIO()
    mathtext.math_to_image('$'+s+'$',buf,dpi=145,color=WHITE,format='png')
    im=Image.open(buf).convert('RGBA')
    # math_to_image uses an opaque white figure; recover transparent ink.
    ar=np.array(im); alpha=255-ar[:,:,:3].min(axis=2)
    # Render with transparent figure instead, preserving the intended ink.
    import matplotlib.pyplot as plt
    fig=plt.figure(figsize=(12,1),dpi=145); fig.patch.set_alpha(0)
    tx=fig.text(0,0,s='$'+s+'$',fontsize=23,color=WHITE)
    fig.canvas.draw(); box=tx.get_window_extent().transformed(fig.dpi_scale_trans.inverted())
    buf=io.BytesIO(); fig.savefig(buf,format='png',transparent=True,bbox_inches=box.expanded(1.03,1.35),pad_inches=0); plt.close(fig)
    im=Image.open(buf).convert('RGBA')
    if im.width>1150 or im.height>60:
        fac=min(1150/im.width,60/im.height); im=im.resize((int(im.width*fac),int(im.height*fac)),Image.Resampling.LANCZOS)
    return im

EQ=[]
def prepare():
    global EQ
    EQ=[equation(s[2]) for s in SCENES]

def text(d,xy,s,n=24,c=WHITE,anchor=None,bold=False): d.text(xy,s,font=font(n,bold),fill=c,anchor=anchor)
def line(d,pts,c=BLUE,w=3): d.line([tuple(map(float,p)) for p in pts],fill=c,width=w,joint='curve')
def poly(d,pts,c=TEAL,outline=None): d.polygon([tuple(map(float,p)) for p in pts],fill=c,outline=outline)
def arrow(d,a,b,c=GOLD,w=3):
    line(d,[a,b],c,w); v=np.array(a)-np.array(b); v=v/(np.linalg.norm(v)+1e-6); p=np.array([-v[1],v[0]])
    poly(d,[b,np.array(b)+13*v+6*p,np.array(b)+13*v-6*p],c)

def panel(d,x=860,y=270,title='',body=''):
    d.rounded_rectangle((x-25,y-30,1215,y+180),radius=16,fill='#172332',outline=GRID,width=2)
    text(d,(x,y),title,24,GOLD,bold=True)
    yy=y+43
    for st in body.split('\n'): text(d,(x,yy),st,22); yy+=33

def axes2(d,origin=(315,490),scale=270,xmax=1.3,ymax=1.25):
    ox,oy=origin
    for t in np.linspace(0,1,5):
        line(d,[(ox+t*scale,oy),(ox+t*scale,oy-ymax*scale)],GRID,1)
        line(d,[(ox,oy-t*scale),(ox+xmax*scale,oy-t*scale)],GRID,1)
    arrow(d,(ox-15,oy),(ox+xmax*scale,oy),MUTED,2); arrow(d,(ox,oy+15),(ox,oy-ymax*scale),MUTED,2)
    text(d,(ox+xmax*scale+12,oy),'x',22,MUTED); text(d,(ox-15,oy-ymax*scale-30),'y',22,MUTED)
    return lambda x,y:(ox+np.asarray(x)*scale,oy-np.asarray(y)*scale)

def P(x,y,z,angle=0):
    # Fixed oblique camera keeps height and floor orientation readable.
    x=np.asarray(x); y=np.asarray(y); z=np.asarray(z)
    return np.stack((480+137*(x-.74*y),410+38*(x+.74*y)-115*z),axis=-1)
def curve3(d,x,y,z,c=BLUE,w=2): line(d,P(x,y,z),c,w)
def floor3(d):
    for a in np.linspace(0,2,9):
        curve3(d,np.array([0,2]),np.array([a,a]),np.zeros(2),GRID,1)
        curve3(d,np.array([a,a]),np.array([0,2]),np.zeros(2),GRID,1)
    for v,label in [((2.2,0,0),'x'),((0,2.2,0),'y'),((0,0,2.3),'z')]:
        a=P(0,0,0); b=P(*v); arrow(d,a,b,MUTED,2); text(d,tuple(b+np.array([6,-22])),label,20,MUTED)
def box(d,x,y,z,dx,dy,c=TEAL):
    for pts,col in [([(x,y,0),(x+dx,y,0),(x+dx,y,z),(x,y,z)],'#247e9c'), ([(x,y,0),(x,y+dy,0),(x,y+dy,z),(x,y,z)],'#205a79'), ([(x,y,z),(x+dx,y,z),(x+dx,y+dy,z),(x,y+dy,z)],c)]:
        poly(d,[P(*q) for q in pts],col,BG)

def columns(d,t,mode):
    floor3(d)
    n=6 if mode=='columns' else 4+int(t*14)
    dx=2/n
    for iy in reversed(range(n)):
        for ix in range(n):
            x=ix*dx; y=iy*dx; h=.4+.27*(x+.5*dx)+.32*math.sin((y+.5*dx)*1.4)
            col=GOLD if mode=='columns' and ix==n//2 and iy==0 else TEAL if (ix+iy)%3 else BLUE
            box(d,x,y,h*ease(min(t*3,1)),dx*.96,dx*.96,col)
    if mode=='columns':
        panel(d,title='ONE COLUMN',body='height: f(x, y)\nbase: Δx × Δy\nvolume: height × base')
    else: panel(d,title=f'{n*n} COLUMNS',body='Smaller pieces.\nCloser fit.\nOne limiting total.')

def fubini(d,t,mode):
    floor3(d)
    n=12; active=min(n-1,int(t*n)); horizontal=mode=='fubini2' and t>.5
    for iy in reversed(range(n)):
        for ix in range(n):
            x=ix*2/n; y=iy*1/n
            chosen=(iy==active if horizontal else ix==active)
            box(d,x,y,(x+y)*.68,2/n*.96,1/n*.96,GOLD if chosen else '#3b92ad')
    panel(d,title='GROUP THE PIECES',body=('Along y first.\nThen add along x.\nSame total: 3' if not horizontal else 'Along x first.\nThen add along y.\nSame total: 3'))

def region(d,t,mode):
    p=axes2(d,(265,510),310)
    xs=np.linspace(0,1,160)
    pts=[p(x,x*x) for x in xs]+[p(x,x) for x in xs[::-1]]
    poly(d,pts,'#204c60'); line(d,[p(x,x*x) for x in xs],BLUE,4); line(d,[p(x,x) for x in xs],TEAL,4)
    if mode=='region':
        x=.08+.84*t; a=p(x,x*x); b=p(x,x)
        line(d,[a,b],GOLD,9)
        text(d,(610,455),'y = x²',24,BLUE); text(d,(420,170),'y = x',24,TEAL)
        panel(d,title='VERTICAL SWEEP',body='freeze x\nenter: y = x²\nleave: y = x')
    else:
        y=.05+.88*t; a=p(y,y); b=p(math.sqrt(y),y); line(d,[a,b],GOLD,9)
        text(d,(610,455),'x = √y',24,BLUE); text(d,(390,170),'x = y',24,TEAL)
        panel(d,title='HORIZONTAL SWEEP',body='freeze y\nenter: x = y\nleave: x = √y')
    for pt in [a,b]: d.ellipse((pt[0]-6,pt[1]-6,pt[0]+6,pt[1]+6),fill=GOLD)
    text(d,(280,540),'Same region. Different strips.',22,MUTED)

def polar(d,t,mode):
    cx,cy,R=430,365,180
    for r in np.linspace(.2,1,5): d.ellipse((cx-R*r,cy-R*r,cx+R*r,cy+R*r),outline=GRID,width=2)
    for a in np.linspace(0,2*math.pi,17): line(d,[(cx,cy),(cx+R*math.cos(a),cy-R*math.sin(a))],GRID,2)
    theta=.45+.7*t; r=.3+.5*t; dr=.16; da=.25
    angles=np.linspace(theta,theta+da,24)
    pts=[(cx+R*r*math.cos(a),cy-R*r*math.sin(a)) for a in angles]+[(cx+R*(r+dr)*math.cos(a),cy-R*(r+dr)*math.sin(a)) for a in angles[::-1]]
    poly(d,pts,GOLD)
    arrow(d,(cx,cy),(cx+R*r*math.cos(theta),cy-R*r*math.sin(theta)),BLUE,3)
    text(d,(cx+50,cy-25),'r',26,BLUE)
    # A magnified tile makes both edge lengths legible.
    q=[(790,450),(1020,410),(1000,290),(805,320)]
    poly(d,q,'#5b5134',GOLD); text(d,(885,458),'r dθ',28,GOLD); text(d,(1030,345),'dr',28,TEAL)
    text(d,(775,210),'ZOOM INTO ONE TILE',22,MUTED)
    text(d,(235,565),'Same angle. Wider arc at larger radius.',22,MUTED)

def dome(d,t):
    floor3(d); angles=np.linspace(0,2*math.pi,150)
    for r in np.linspace(.1,1,10): curve3(d,1+r*np.cos(angles),1+r*np.sin(angles),np.full_like(angles,1.8*(1-r*r)),TEAL,2)
    for a in np.linspace(0,2*math.pi,24):
        r=np.linspace(0,1,80); curve3(d,1+r*np.cos(a),1+r*np.sin(a),1.8*(1-r*r),BLUE,2)
    r=.1+.85*t; curve3(d,1+r*np.cos(angles),1+r*np.sin(angles),np.full_like(angles,1.8*(1-r*r)),GOLD,4)
    panel(d,title='UNIT-DISK DOME',body='height = 1 − r²\narea piece = r dr dθ\nvolume = π / 2')

def mass(d,t,mode):
    x0,y0,s=260,195,320
    for j in range(16):
        for i in range(16):
            col=(int(40+i*6),int(100+i*6),int(130+i*5))
            d.rectangle((x0+i*s/16,y0+j*s/16,x0+(i+1)*s/16-2,y0+(j+1)*s/16-2),fill=col)
    text(d,(260,535),'δ(x, y) = 1 + x',26,BLUE)
    if mode=='centroid':
        xx=x0+s*lerp(.5,5/9,ease(t)); yy=y0+s/2
        d.ellipse((xx-10,yy-10,xx+10,yy+10),fill=GOLD)
        line(d,[(xx-22,yy),(xx+22,yy)],BG,2); line(d,[(xx,yy-22),(xx,yy+22)],BG,2)
        panel(d,title='CENTER OF MASS',body='m = 3/2\nx̄ = 5/9\nȳ = 1/2')
    else: panel(d,title='WHAT IS ON THE TILE?',body='height → volume\ndensity → mass\nsum / area → average')

def tetra(d,t,mode):
    floor3(d)
    if mode=='triple':
        for z in range(3):
            for y in reversed(range(5)):
                for x in range(5):
                    a=P(x*.3,y*.3,z*.3); b=P(x*.3+.27,y*.3+.27,z*.3+.27)
                    # Draw actual floating cube faces.
                    vertices=[(x*.3+dx,y*.3+dy,z*.3+dz) for dx,dy,dz in [(0,0,0),(.27,0,0),(.27,.27,0),(0,.27,0),(0,0,.27),(.27,0,.27),(.27,.27,.27),(0,.27,.27)]]
                    for inds,col in [([0,1,5,4],'#286480'),([0,3,7,4],'#205269'),([4,5,6,7],TEAL if z<2 else BLUE)]: poly(d,[P(*vertices[k]) for k in inds],col,BG)
        panel(d,title='TINY BOXES',body='1 × dV → volume\nδ × dV → mass\ndV = dx dy dz')
    else:
        v=[P(0,0,0),P(2,0,0),P(0,2,0),P(0,0,2)]
        poly(d,[v[0],v[1],v[2]],'#204457'); poly(d,[v[1],v[2],v[3]],'#20576c',BLUE)
        for a,b in [(0,1),(0,2),(0,3),(1,2),(1,3),(2,3)]: line(d,[v[a],v[b]],BLUE,3)
        x=.15+1.25*t; y=.25; z=2-x-y
        line(d,[P(x,y,0),P(x,y,z)],GOLD,9)
        panel(d,title='INSIDE → OUT',body='z: floor to sloping roof\ny: across the shadow\nx: across the triangle')

def cylinder(d,t):
    floor3(d); a=np.linspace(0,2*math.pi,150)
    for z in np.linspace(0,1.7,8): curve3(d,1+.85*np.cos(a),1+.85*np.sin(a),np.full_like(a,z),TEAL,2)
    for theta in np.linspace(0,2*math.pi,18): curve3(d,np.full(2,1+.85*math.cos(theta)),np.full(2,1+.85*math.sin(theta)),[0,1.7],BLUE,2)
    z=1.7*t; curve3(d,1+.85*np.cos(a),1+.85*np.sin(a),np.full_like(a,z),GOLD,4)
    panel(d,title='POLAR FLOOR + HEIGHT',body='radial: dr\nangular: r dθ\nvertical: dz')

def sphere(d,t,mode):
    cx,cy,R=460,370,175
    def sp(phi,theta,r=1):
        x=r*np.sin(phi)*np.cos(theta); y=r*np.sin(phi)*np.sin(theta); z=r*np.cos(phi)
        return np.stack((cx+R*(x-.35*y),cy+R*(.25*y+.12*x-z)),axis=-1)
    aa=np.linspace(0,2*math.pi,150); pp=np.linspace(0,math.pi,110)
    for ph in np.linspace(.15,math.pi-.15,11): line(d,sp(np.full_like(aa,ph),aa),GRID,2)
    for th in np.linspace(0,2*math.pi,18): line(d,sp(pp,np.full_like(pp,th)),BLUE,1)
    ph=.15+(math.pi-.3)*t
    line(d,sp(np.full_like(aa,ph),aa),GOLD,4)
    if mode=='spherefactor':
        ph=.5+1.8*t; th=-.8; dp=.25; dt=.3
        corners=[(ph,th),(ph+dp,th),(ph+dp,th+dt),(ph,th+dt)]
        for r,col in [(1,'#78613c'),(1.16,'#b69653')]: poly(d,[sp(p,a,r) for p,a in corners],col,GOLD)
        for p,a in corners: line(d,[sp(p,a),sp(p,a,1.16)],TEAL,3)
        text(d,(240,165),'A shell block has three short edges.',22,GOLD)
    endpoint=sp(ph,.3); arrow(d,(cx,cy),endpoint,TEAL,3)
    text(d,(cx+28,cy-55),'ρ',28,TEAL)
    if mode=='sphere': panel(d,title='THREE COORDINATES',body='ρ: distance from origin\nθ: angle around z\nφ: angle down from +z')
    elif mode=='spherefactor': panel(d,title='THREE EDGE LENGTHS',body='radial: dρ\nmeridian: ρ dφ\nlatitude: ρ sinφ dθ')
    else: panel(d,title='BALL OF RADIUS a',body='radial total: a³ / 3\npolar total: 2\nazimuth total: 2π')
    text(d,(295,565),'Latitude circles shrink toward the poles.',22,MUTED)

def jacobian(d,t,mode):
    if mode=='ellipse':
        for i,(cx,rx) in enumerate([(300,110),(850,220)]):
            ry=110; d.ellipse((cx-rx,350-ry,cx+rx,350+ry),fill='#204c60',outline=BLUE,width=3)
            for y in np.linspace(-.9,.9,11):
                extent=math.sqrt(1-y*y); line(d,[(cx-rx*extent,350-ry*y),(cx+rx*extent,350-ry*y)],GRID,2)
            text(d,(cx,520),'unit disk' if i==0 else 'ellipse',28,TEAL,anchor='mm')
        arrow(d,(450,350),(580,350)); text(d,(505,300),'× 2',28,GOLD,anchor='mm')
        text(d,(800,180),'Every tile doubles its area.',24,GOLD)
    else:
        a=np.array([300,455]); b=np.array([155,0]); c=np.array([0,-155]); k=ease(t)
        dest=np.array([800,455]); b2=np.array([210,-55]); c2=np.array([80,-165])
        for origin,u,v in [(a,b,c),(dest,lerp(b,b2,k),lerp(c,c2,k))]:
            for z in np.linspace(0,1,7):
                line(d,[origin+z*u,origin+z*u+v],BLUE,2); line(d,[origin+z*v,origin+z*v+u],TEAL,2)
            pts=[origin,origin+u/6,origin+u/6+v/6,origin+v/6]; poly(d,pts,GOLD)
        arrow(d,(500,365),(670,365)); text(d,(300,520),'parameter plane (u, v)',24,MUTED,anchor='mm'); text(d,(930,520),'physical plane (x, y)',24,MUTED,anchor='mm')
        text(d,(765,190),'Local area scale = |det J|',26,GOLD)

def surface(d,t,mode):
    floor3(d)
    slope=lerp(.05,.7,ease(t)) if mode=='surface' else .7
    for x in np.linspace(0,1.8,10):
        y=np.linspace(0,1.8,30); curve3(d,np.full_like(y,x),y,slope*(x+y),TEAL,2)
    for y in np.linspace(0,1.8,10):
        x=np.linspace(0,1.8,30); curve3(d,x,np.full_like(x,y),slope*(x+y),BLUE,2)
    xy=[(.65,.65),(1.15,.65),(1.15,1.15),(.65,1.15)]
    poly(d,[P(x,y,0) for x,y in xy],'#635332',GOLD)
    poly(d,[P(x,y,slope*(x+y)) for x,y in xy],'#2d8e87',TEAL)
    for x,y in xy: line(d,[P(x,y,0),P(x,y,slope*(x+y))],MUTED,1)
    panel(d,title='PATCH / SHADOW',body=('tilt increases area\nflat: multiplier = 1\nsloped: multiplier > 1' if mode=='surface' else 'slope along x: 1\nslope along y: 1\narea factor: √3'))

def probability(d,t):
    x0,y0,s=260,190,330
    for j in range(20):
        for i in range(20):
            col=GOLD if i<int(20*t) and j>7 else '#327c96'
            d.rectangle((x0+i*s/20,y0+j*s/20,x0+(i+1)*s/20-2,y0+(j+1)*s/20-2),fill=col)
    panel(d,title='SUM OVER A REGION',body='density × area\n= probability piece\nall pieces sum to 1')
    text(d,(250,548),'Highlighted tiles = an event region D',22,MUTED)

def intro(d,t,mode):
    if mode=='intro':
        for i,(sym,label,col) in enumerate([('∫','length',BLUE),('∬','area',TEAL),('∭','volume',GOLD)]):
            x=270+i*350; text(d,(x,280),sym,100,col,anchor='mm'); text(d,(x,405),label,28,col,anchor='mm')
        text(d,(640,520),'What are the pieces?  How big is each one?',30,WHITE,anchor='mm')
    else:
        labels=[('1','SKETCH','Draw the region.'),('2','CHOOSE','Fit coordinates to shape.'),('3','MEASURE','Find the tiny piece.'),('4','SWEEP','Read the bounds.'),('5','ADD','Integrate; check units.')]
        for i,(num,head,body) in enumerate(labels):
            y=190+74*i; d.ellipse((220,y-15,260,y+25),fill=TEAL if i<=int(t*5) else GRID); text(d,(240,y+4),num,22,BG,anchor='mm'); text(d,(290,y),head,24,GOLD,bold=True); text(d,(500,y),body,24,WHITE)

def caption_parts(s):
    words=s.split(); parts=[]; cur=[]
    for w in words:
        if len(' '.join(cur+[w]))>98: parts.append(' '.join(cur)); cur=[]
        cur.append(w)
    if cur: parts.append(' '.join(cur))
    return parts

def frame(idx,t,caption=''):
    title,kind,eq,narr=SCENES[idx]
    im=Image.new('RGB',(W,H),BG); d=ImageDraw.Draw(im)
    text(d,(55,26),'THE GEOMETRY OF ADDING',18,TEAL,bold=True); text(d,(1225,29),f'{idx+1:02d} / {len(SCENES):02d}',18,MUTED,anchor='ra')
    text(d,(55,64),title,32,WHITE,bold=True)
    line(d,[(55,116),(1225,116)],GRID,2)
    if kind in ['columns','refine']: columns(d,t,kind)
    elif kind in ['fubini','fubini2']: fubini(d,t,kind)
    elif kind in ['region','reverse']: region(d,t,kind)
    elif kind=='polar': polar(d,t,kind)
    elif kind=='dome': dome(d,t)
    elif kind in ['mass','centroid']: mass(d,t,kind)
    elif kind in ['triple','tetra']: tetra(d,t,kind)
    elif kind=='cylinder': cylinder(d,t)
    elif kind in ['sphere','spherefactor','ball']: sphere(d,t,kind)
    elif kind in ['jacobian','ellipse']: jacobian(d,t,kind)
    elif kind in ['surface','surfaceexample']: surface(d,t,kind)
    elif kind=='probability': probability(d,t)
    else: intro(d,t,kind)
    # Separate formula and caption bands keep labels clear.
    d.rounded_rectangle((40,588,1240,654),radius=12,fill='#182536')
    e=EQ[idx]; im.paste(e,((W-e.width)//2,621-e.height//2),e)
    if caption:
        lines=textwrap.wrap(caption,width=108)
        for j,s in enumerate(lines[:2]): text(d,(640,667+j*24),s,20,WHITE,anchor='mt')
    d.rectangle((0,716,int(W*(idx+t)/len(SCENES)),719),fill=TEAL)
    return im

def duration(p):
    r=subprocess.run([FF,'-i',str(p)],capture_output=True,text=True)
    m=re.search(r'Duration: (\d+):(\d+):([\d.]+)',r.stderr)
    if not m: raise RuntimeError(r.stderr[-1200:])
    return int(m[1])*3600+int(m[2])*60+float(m[3])

async def narrate():
    import edge_tts
    sem=asyncio.Semaphore(2)
    async def one(i,s):
        p=AUDIO/f'{s[1]}.mp3'
        if p.exists() and p.stat().st_size>1000: return
        async with sem:
            for attempt in range(3):
                try:
                    await edge_tts.Communicate(s[3],voice='en-GB-RyanNeural',rate='-8%').save(str(p))
                    print(f'Narration {i+1}/{len(SCENES)} ready',flush=True); return
                except Exception:
                    if attempt==2: raise
                    await asyncio.sleep(2)
    await asyncio.gather(*(one(i,s) for i,s in enumerate(SCENES)))

def stamp(s):
    ms=round(s*1000); h,ms=divmod(ms,3600000); m,ms=divmod(ms,60000); sec,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{sec:02},{ms:03}'

def render():
    offset=0; subtitles=[]; chapter=[]
    for i,s in enumerate(SCENES):
        ap=AUDIO/f'{s[1]}.mp3'; spoken=duration(ap); dur=spoken+1.8; frames=math.ceil(dur*FPS); dur=frames/FPS
        chapter.append({'title':s[0],'start':round(offset,3),'duration':round(dur,3)})
        captions=caption_parts(s[3]); weights=np.array([len(x) for x in captions]); edges=np.r_[0,np.cumsum(weights)/sum(weights)*spoken]
        for j,cap in enumerate(captions): subtitles.append((offset+edges[j],offset+edges[j+1],cap))
        video=OUT/f'scene_{i:02d}.mp4'
        if not video.exists():
            cmd=[FF,'-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s',f'{W}x{H}','-r',str(FPS),'-i','pipe:0','-i',str(ap),'-af','apad','-t',str(dur),'-c:v','libx264','-preset','fast','-crf','20','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart',str(video)]
            proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
            for k in range(frames):
                sec=k/FPS; t=k/max(1,frames-1); ci=min(len(captions)-1,max(0,int(np.searchsorted(edges,sec,side='right')-1)))
                im=frame(i,t,captions[ci] if sec<=spoken else '')
                proc.stdin.write(im.tobytes())
            proc.stdin.close()
            if proc.wait(): raise RuntimeError(f'Encoding scene {i} failed')
        print(f'Rendered {i+1}/{len(SCENES)}: {dur:.1f}s',flush=True); offset+=dur
    (OUT/'chapters.json').write_text(json.dumps(chapter,indent=2))
    (OUT/'captions.srt').write_text('\n\n'.join(f'{i+1}\n{stamp(a)} --> {stamp(b)}\n'+ '\n'.join(textwrap.wrap(s,100)) for i,(a,b,s) in enumerate(subtitles)))
    manifest=OUT/'concat.txt'; manifest.write_text('\n'.join(f"file 'scene_{i:02d}.mp4'" for i in range(len(SCENES))))
    meta=OUT/'chapters.ffmeta'; meta.write_text(';FFMETADATA1\ntitle=The Geometry of Adding — Multiple Integrals\nartist=Original educational animation\n'+''.join(f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(c['start']*1000)}\nEND={round((c['start']+c['duration'])*1000)}\ntitle={c['title']}\n" for c in chapter))
    subprocess.run([FF,'-y','-loglevel','error','-f','concat','-safe','0','-i',str(manifest),'-i',str(meta),'-i',str(OUT/'captions.srt'),'-map','0:v','-map','0:a','-map','2:0','-map_metadata','1','-map_chapters','1','-c:v','copy','-c:a','aac','-b:a','128k','-af','aresample=async=1:first_pts=0','-c:s','mov_text','-metadata:s:s:0','language=eng','-movie_timescale','1000','-movflags','+faststart',str(OUT/'chapter15_multiple_integrals.mp4')],check=True)
    print(f'COMPLETE: {offset/60:.2f} minutes',flush=True)

def stills():
    prepare(); thumbs=[]
    for i in range(len(SCENES)):
        im=frame(i,.57); im.save(OUT/f'preview_{i:02d}.png'); thumbs.append(im.resize((384,216)))
    sheet=Image.new('RGB',(384*4,216*math.ceil(len(thumbs)/4)),BG)
    for i,im in enumerate(thumbs): sheet.paste(im,((i%4)*384,(i//4)*216))
    sheet.save(OUT/'storyboard.jpg',quality=93)
    frame(8,.55).save(OUT/'poster.png')

if __name__=='__main__':
    if '--audio' in sys.argv: asyncio.run(narrate())
    elif '--stills' in sys.argv: stills()
    else: prepare(); render()
