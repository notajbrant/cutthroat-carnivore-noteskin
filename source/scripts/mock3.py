import numpy as np, math, random, re
from PIL import Image
A='build/art2/'; random.seed(11)
def L(n): return Image.open(A+n).convert('RGBA')
def find(prefix):
    import os
    return [f for f in os.listdir(A) if f.startswith(prefix)][0]
shard_tab=[(m.group(1),float(m.group(2)),float(m.group(3))) for m in re.finditer(r'tex = "([^"]+)", x = ([-\d.]+), y = ([-\d.]+)', open(A+'_CC Shards.lua').read())]
def canvas(W,H):
    bg=np.zeros((H,W,3)); yy=np.linspace(0,1,H)[:,None]; bg[:]=np.stack([0.05+0.03*yy,0.04+0*yy,0.055+0.02*yy],-1); return bg
def put(bg,img,cx,cy,add=False,alpha=1.0):
    H,W=bg.shape[:2]; a=np.asarray(img).astype(float)/255; h,w=a.shape[:2]; x0,y0=int(round(cx-w/2)),int(round(cy-h/2))
    xs,ys=max(0,x0),max(0,y0); xe,ye=min(W,x0+w),min(H,y0+h)
    if xs>=xe or ys>=ye: return
    s=a[ys-y0:ye-y0,xs-x0:xe-x0]; k=s[...,3:4]*alpha; reg=bg[ys:ye,xs:xe]
    reg[:]=reg+s[...,:3]*k if add else s[...,:3]*k+reg*(1-k)
def ease_out(t): return 1-(1-t)**3
def explosion(bg,cx,cy,t,seed=3,scale=2.0):
    """t in seconds since the hit. scale = px per noteskin unit."""
    r=random.Random(seed)
    if t<0.10:
        a=1-t/0.10; put(bg,L(find('_CC FX Smoke')).resize((int(100*scale*(0.8+t*3)),)*2).rotate(40),cx,cy,alpha=0.9*min(1,t/0.03+0.3))
    else:
        put(bg,L(find('_CC FX Smoke')).resize((int(100*scale*(1.1+t)),)*2).rotate(40+t*60),cx,cy,alpha=max(0,0.8-(t-0.1)*2))
    fa=max(0,1-t/0.16); put(bg,L(find('_CC FX Flash')).resize((int(96*scale*(0.7+t*2)),)*2),cx,cy,add=True,alpha=fa)
    ra=max(0,1-t/0.2); put(bg,L(find('_CC FX Rays')).resize((int(110*scale*(0.6+t*2.5)),)*2).rotate(17),cx,cy,add=True,alpha=ra*0.8)
    if t<0.12:
        lt=L(find('_CC FX Lightning')); fr=int(t/0.03)%8; put(bg,lt.crop((fr*256,0,fr*256+256,256)).resize((int(110*scale),)*2).rotate(r.random()*360),cx,cy,add=True,alpha=1-t/0.12)
    # shards: fly outward from the arrow centre, tumble, fade
    for i,(tex,sx,sy) in enumerate(shard_tab):
        img=L(find(tex)); ang=math.atan2(sy+0.01,sx+0.01)+r.uniform(-0.35,0.35); dist=r.uniform(38,70)
        p=ease_out(min(1,t/0.42)); ox=sx+math.cos(ang)*dist*p; oy=sy+math.sin(ang)*dist*p+ 25*(t**2)*4
        rot=r.uniform(-300,300)*p; a=1.0 if t<0.25 else max(0,1-(t-0.25)/0.2)
        im=img.resize((int(img.width*scale/2*(1-0.25*p)),int(img.height*scale/2*(1-0.25*p))),Image.LANCZOS).rotate(rot,expand=True,resample=Image.BICUBIC)
        put(bg,im,cx+ox*scale,cy+oy*scale,alpha=a)
    for k in range(18):   # micro debris spray
        ang=r.random()*2*math.pi; dist=r.uniform(40,105)*ease_out(min(1,t/0.35)); a=max(0,1-t/0.45)
        im=L(find('_CC FX Debris')).resize((int(16*scale*r.uniform(0.5,1.0)),)*2).rotate(r.random()*360)
        put(bg,im,cx+math.cos(ang)*dist*scale,cy+math.sin(ang)*dist*scale,alpha=a)
    for k in range(12):   # spark streaks
        ang=r.random()*2*math.pi; dist=r.uniform(30,85)*ease_out(min(1,t/0.25)); a=max(0,1-t/0.3)
        im=L(find('_CC FX Spark')).resize((int(32*scale*r.uniform(0.6,1.2)),int(8*scale)),Image.LANCZOS).rotate(-math.degrees(ang),expand=True)
        put(bg,im,cx+math.cos(ang)*dist*scale,cy+math.sin(ang)*dist*scale,add=True,alpha=a)
    for k in range(10):   # embers drift up
        ang=r.random()*2*math.pi; dist=r.uniform(15,45)*ease_out(min(1,t/0.3)); a=max(0,1-t/0.7)
        put(bg,L(find('_CC FX Ember')).resize((int(16*scale*r.uniform(0.6,1.1)),)*2),cx+math.cos(ang)*dist*scale,cy+(math.sin(ang)*dist-60*t)*scale,add=True,alpha=a)
# --- timeline strip ---
times=[0.0,0.05,0.12,0.22,0.35]
bg=canvas(len(times)*300,300)
note=L(find('_CC Tap Note Quant')); rec=L(find('_CC Receptor'))
for i,t in enumerate(times):
    cx,cy=150+i*300,150
    put(bg,rec.crop((0,0,128,128)),cx,cy)
    if t==0: put(bg,note.crop((0,0,128,128)),cx,cy)
    else: explosion(bg,cx,cy,t)
Image.fromarray((np.clip(bg,0,1)*255).astype(np.uint8)).save('build/shatter_timeline.png')
# --- gameplay frame ---
W,H=760,1000; bg=canvas(W,H)
ROT={0:90,1:0,2:180,3:-90}
def rot(img,deg): return img.rotate(-deg,resample=Image.BICUBIC)
cols=[W/2-192,W/2-64,W/2+64,W/2+192]; ry=150
def nf(q,f=0): return note.crop((f*128,q*128,(f+1)*128,(q+1)*128))
hb=L(find('Down Hold Body Active')); hc=L(find('Down Hold BottomCap Active'))
for y in range(ry,600,128): put(bg,hb,cols[2],y+64)
put(bg,hc,cols[2],600+64+32-10)
aura=L(find('_CC Receptor Aura'))
for i,c in enumerate(cols):
    if i==1: put(bg,aura.crop((224*2,0,224*3,224)),c,ry,add=True)
    put(bg,rot(rec.crop((0,0,128,128)),ROT[i]),c,ry)
put(bg,rot(rec.crop((128,0,256,128)),ROT[0]),cols[0],ry,add=True,alpha=0.8)
put(bg,rot(nf(0,1),ROT[2]),cols[2],ry)   # hold head sitting in the receptor
orb=L(find('_CC FX HoldOrb')).crop((128*2,0,128*3,128)); put(bg,orb,cols[2],ry,add=True)
stream=[(0,330,0,0),(3,395,1,1),(1,460,0,2),(0,525,1,3),(3,590,0,0),(1,655,3,1),(0,720,0,2),(3,785,1,3),(1,850,0,0),(2,850,2,1),(0,915,1,2),(3,980,0,3)]
for c,y,q,f in stream: put(bg,rot(nf(q,f),ROT[c]),cols[c],y)
explosion(bg,cols[1],ry,0.12)
Image.fromarray((np.clip(bg,0,1)*255).astype(np.uint8)).save('build/mock_gameplay_v3.png')
