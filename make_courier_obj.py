"""Create an editable low-poly Parcel Panic courier OBJ for Blender import."""
import math, os

ROOT=os.path.dirname(os.path.abspath(__file__))
OUT=os.path.join(ROOT,"Game","Assets","Characters","ParcelPanicCourier")
os.makedirs(OUT,exist_ok=True)
OBJ=os.path.join(OUT,"ParcelPanicCourier.obj")
MTL=os.path.join(OUT,"ParcelPanicCourier.mtl")
materials={
 "Purple":(0.26,0.14,0.60), "Pink":(0.94,0.22,0.49), "Cyan":(0.04,0.70,0.84),
 "Lime":(0.62,0.86,0.16), "Skin":(0.77,0.51,0.34), "Navy":(0.09,0.12,0.22),
 "Cream":(0.95,0.93,0.85), "Cardboard":(0.62,0.39,0.20), "Tape":(0.98,0.76,0.34)
}
verts=[]; faces=[]; groups=[]

def mesh(name,mat,vs,fs):
    start=len(verts); verts.extend(vs)
    for f in fs: faces.append((name,mat,tuple(start+i for i in f)))

def box(name,mat,c,s):
    x,y,z=c; a,b,d=[v/2 for v in s]
    vs=[(x+sx*a,y+sy*b,z+sz*d) for sx,sy,sz in [(-1,-1,-1),(1,-1,-1),(1,1,-1),(-1,1,-1),(-1,-1,1),(1,-1,1),(1,1,1),(-1,1,1)]]
    fs=[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)]
    mesh(name,mat,vs,fs)

def ball(name,mat,c,r,segments=8,rings=5):
    x,y,z=c; rx,ry,rz=r; vs=[(x,y,z+rz)]
    for j in range(1,rings):
        phi=math.pi*j/rings
        for i in range(segments):
            t=2*math.pi*i/segments
            vs.append((x+rx*math.sin(phi)*math.cos(t),y+ry*math.sin(phi)*math.sin(t),z+rz*math.cos(phi)))
    vs.append((x,y,z-rz)); bot=len(vs)-1; fs=[]
    for i in range(segments): fs.append((0,1+i,1+(i+1)%segments))
    for j in range(rings-2):
        a=1+j*segments; b=a+segments
        for i in range(segments): fs.append((a+i,b+i,b+(i+1)%segments,a+(i+1)%segments))
    a=1+(rings-2)*segments
    for i in range(segments): fs.append((a+i,bot,a+(i+1)%segments))
    mesh(name,mat,vs,fs)

def beam(name,mat,a,b,r,segments=8):
    ax,ay,az=a; bx,by,bz=b
    dx,dy,dz=bx-ax,by-ay,bz-az; L=math.sqrt(dx*dx+dy*dy+dz*dz)
    ux,uy,uz=dx/L,dy/L,dz/L
    # perpendicular basis, with graceful fallback when the beam is vertical
    ref=(0,1,0) if abs(uz)>.9 else (0,0,1)
    vx=uy*ref[2]-uz*ref[1]; vy=uz*ref[0]-ux*ref[2]; vz=ux*ref[1]-uy*ref[0]
    vl=math.sqrt(vx*vx+vy*vy+vz*vz); vx,vy,vz=vx/vl,vy/vl,vz/vl
    wx=uy*vz-uz*vy; wy=uz*vx-ux*vz; wz=ux*vy-uy*vx
    vs=[]
    for center in (a,b):
        for i in range(segments):
            t=2*math.pi*i/segments
            vs.append((center[0]+r*(vx*math.cos(t)+wx*math.sin(t)),center[1]+r*(vy*math.cos(t)+wy*math.sin(t)),center[2]+r*(vz*math.cos(t)+wz*math.sin(t))))
    fs=[tuple(reversed(range(segments))),tuple(range(segments,2*segments))]
    for i in range(segments): fs.append((i,(i+1)%segments,(i+1)%segments+segments,i+segments))
    mesh(name,mat,vs,fs)

# Upright character faces +Y; the cyan pack sits on the back (-Y).
box("Jacket", "Pink", (0,0,1.55),(.76,.46,.76))
box("Jacket hem", "Purple",(0,.015,1.19),(.72,.45,.13))
beam("Left thigh","Purple",(-.2,0,1.17),(-.29,.16,.70),.145)
ball("Left knee","Purple",(-.29,.16,.70),(.15,.15,.15))
beam("Left shin","Purple",(-.29,.16,.68),(-.34,.39,.25),.105)
box("Left trainer","Navy",(-.34,.48,.12),(.25,.40,.20))
box("Left sole","Cream",(-.34,.49,.045),(.27,.42,.065))
beam("Right thigh","Purple",(.2,0,1.17),(.28,-.02,.73),.145)
ball("Right knee","Purple",(.28,-.02,.73),(.15,.15,.15))
beam("Right shin","Purple",(.28,-.02,.71),(.38,-.31,.29),.105)
box("Right trainer","Navy",(.38,-.40,.13),(.25,.40,.20))
box("Right sole","Cream",(.38,-.41,.045),(.27,.42,.065))
ball("Head","Skin",(0,.025,2.16),(.30,.28,.34))
ball("Hair","Navy",(0,-.015,2.33),(.31,.29,.20))
ball("Backwards cap crown","Purple",(0,-.045,2.43),(.34,.32,.20))
box("Backwards cap brim","Purple",(0,-.36,2.39),(.40,.34,.055))
box("Cap lime band","Lime",(0,-.11,2.32),(.47,.035,.06))
box("Delivery backpack","Cyan",(0,-.31,1.58),(.69,.32,.73))
box("Backpack pocket","Cyan",(0,-.493,1.45),(.47,.08,.27))
box("Backpack flap","Lime",(0,-.505,1.83),(.57,.075,.13))
for x in (-.25,.25): box("Backpack strap","Purple",(x,-.105,1.60),(.075,.075,.55))
box("Backpack badge","Cream",(0,-.545,1.60),(.18,.025,.15))
beam("Left upper arm","Pink",(-.39,-.01,1.79),(-.55,-.11,1.48),.115)
ball("Left elbow","Skin",(-.55,-.11,1.48),(.12,.12,.12))
beam("Left forearm","Pink",(-.55,-.11,1.48),(-.48,-.30,1.27),.085)
ball("Left hand","Skin",(-.48,-.30,1.24),(.105,.09,.10))
beam("Right upper arm","Pink",(.39,-.01,1.79),(.55,.10,1.54),.115)
ball("Right elbow","Skin",(.55,.10,1.54),(.12,.12,.12))
beam("Right forearm","Pink",(.55,.10,1.54),(.52,.34,1.42),.085)
ball("Right hand","Skin",(.52,.34,1.40),(.105,.09,.10))
box("Held parcel","Cardboard",(.58,.48,1.39),(.28,.28,.27))
box("Parcel tape","Tape",(.58,.48,1.39),(.055,.295,.28))
box("Parcel label","Cream",(.58,.63,1.41),(.11,.012,.07))

with open(MTL,"w") as f:
    for n,c in materials.items():
        f.write(f"newmtl {n}\nKd {c[0]} {c[1]} {c[2]}\nKa 0.08 0.08 0.08\nKs 0.05 0.05 0.05\nNs 12\n\n")
with open(OBJ,"w") as f:
    f.write("# Parcel Panic courier character | low-poly, upright, faces +Y, units = metres\n")
    f.write("mtllib ParcelPanicCourier.mtl\n")
    for x,y,z in verts: f.write(f"v {x:.5f} {y:.5f} {z:.5f}\n")
    active=None; material=None
    for name,matname,face in faces:
        if name!=active: f.write(f"g {name.replace(' ','_')}\n"); active=name
        if matname!=material: f.write(f"usemtl {matname}\n"); material=matname
        f.write("f "+" ".join(str(i+1) for i in face)+"\n")
print(OBJ)
