"""Editable character study, modelled from the supplied Parcel Panic concept.

Run in Blender's Python console.  Builds a new scene and saves a separate file.
All surfaces, hair locks, clothing, fingers and accessories are editable geometry.
"""
import bpy, math, os, json, traceback
from mathutils import Vector
from math import sin, cos, pi, exp

ROOT = '/Users/joyhowlader/Documents/ChatGPT/final year project'
OUT = os.path.join(ROOT, 'Game/Assets/Characters/ParcelPanicCourier')
REFERENCE = '/Users/joyhowlader/.codex/generated_images/01a0cf41-8a6f-7790-8208-ab7c95752441/exec-86d51733-e405-4b24-9ae1-1b01373d8484.png'
os.makedirs(OUT, exist_ok=True)

def build():
    global COLL
    for obj in list(bpy.data.objects): bpy.data.objects.remove(obj, do_unlink=True)
    for c in list(bpy.data.collections):
        if c.users == 0: bpy.data.collections.remove(c)
    scene=bpy.context.scene
    COLL=scene.collection

    def group(name):
        global COLL
        COLL=bpy.data.collections.new(name); scene.collection.children.link(COLL)
        return COLL

    def link_obj(obj):
        for c in list(obj.users_collection): c.objects.unlink(obj)
        COLL.objects.link(obj)
        return obj

    def linear(v): return v/12.92 if v <= .04045 else ((v+.055)/1.055)**2.4
    def rgb(code): return tuple(linear(int(code[i:i+2],16)/255) for i in (0,2,4))
    def mat(name,code,rough=.55,fabric=False,metal=0,skin=False):
        m=bpy.data.materials.new(name); color=rgb(code); m.diffuse_color=(*color,1); m.use_nodes=True
        n=m.node_tree.nodes; p=n.get('Principled BSDF'); p.inputs['Base Color'].default_value=(*color,1)
        p.inputs['Roughness'].default_value=rough; p.inputs['Metallic'].default_value=metal
        if 'Specular IOR Level' in p.inputs:p.inputs['Specular IOR Level'].default_value=.24 if fabric else .32
        for label in ('Subsurface Weight','Subsurface'):
            if skin and label in p.inputs: p.inputs[label].default_value=.065
        if fabric:
            noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=210;noise.inputs['Detail'].default_value=2
            bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.13;bump.inputs['Distance'].default_value=.007
            m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height']);m.node_tree.links.new(bump.outputs['Normal'],p.inputs['Normal'])
        return m

    skin=mat('01 • warm tan skin','CE9169',.52,skin=True)
    skin_shadow=mat('Skin • ear interior and warm lips','BA765B',.58,skin=True)
    lip=mat('Mouth • muted rose','8C4D40',.55)
    hair=mat('02 • chestnut brown hair','4D2818',.56)
    hair_hi=mat('Hair • strand highlights','724126',.59)
    hair_dark=mat('Hair • grooves and brows','372016',.48)
    eye_white=mat('Eyes • warm ivory','FFF7E7',.24)
    iris=mat('Eyes • brown iris','713C1B',.25)
    iris_light=mat('Eyes • amber inner iris','A45F2A',.29)
    pupil=mat('Eyes • dark pupils','17100C',.16)
    glint=mat('Eyes • catchlights','FFFFFF',.12)
    purple=mat('03 • violet cap','783DD1',.52,True)
    purple_dark=mat('Cap • inner band','4E2794',.67,True)
    pants=mat('04 • purple cargo fabric','7550B4',.69,True)
    pants_seam=mat('Cargo • dark violet seams','543587',.73)
    pants_edge=mat('Cargo • stitch thread','A17BC9',.71)
    pink=mat('05 • hot pink jacket','EB2C83',.57,True)
    pink_inner=mat('Jacket • inner facing','AD175B',.65,True)
    pink_edge=mat('Jacket • raised seam thread','F46CA5',.64)
    shirt=mat('06 • cream undershirt','F3EFF2',.75,True)
    cyan=mat('07 • cyan delivery backpack','09ABC8',.6,True)
    teal=mat('Backpack • dark piping','08728A',.7)
    lime=mat('08 • lime accents','C6E635',.5)
    webbing=mat('09 • dark navy webbing','263744',.78,True)
    shoes=mat('10 • navy trainers','2D344E',.56)
    shoe_panel=mat('Trainer • suede panels','3C465E',.77,True)
    sole=mat('Trainer • off white rubber sole','E2E0D7',.65)
    lace=mat('Trainer • grey laces','8991A0',.77)
    metal=mat('Hardware • silver zipper','BFC5CB',.28,metal=.65)
    cardboard=mat('11 • kraft cardboard','B77F48',.82,True)
    cardboard_edge=mat('Parcel • cut edges','9D6939',.88)
    tape=mat('Parcel • beige packing tape','D8BD8A',.52)
    floor=mat('Studio • off white','F2F0ED',.82)

    def mesh(name,verts,faces,material,sub=0):
        data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
        ob=bpy.data.objects.new(name,data);COLL.objects.link(ob)
        if material:data.materials.append(material)
        for f in data.polygons:f.use_smooth=True
        if sub:
            s=ob.modifiers.new('Surface smoothing','SUBSURF');s.levels=sub;s.render_levels=sub
        return ob

    def sphere(name,loc,scale,material,rot=None,seg=48,rings=32):
        bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=loc)
        ob=link_obj(bpy.context.object);ob.name=name;ob.scale=scale
        if rot:ob.rotation_euler=rot
        ob.data.materials.append(material)
        for f in ob.data.polygons:f.use_smooth=True
        return ob

    def box(name,loc,dim,material,bevel=.045,rot=None):
        bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
        ob=link_obj(bpy.context.object);ob.name=name
        # Set vertex coordinates directly; no context-dependent transform operator.
        for v in ob.data.vertices:v.co.x*=dim[0];v.co.y*=dim[1];v.co.z*=dim[2]
        if rot:ob.rotation_euler=rot
        ob.data.materials.append(material)
        if bevel:
            mod=ob.modifiers.new('Rounded construction edges','BEVEL');mod.width=bevel;mod.segments=5
            ob.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
        return ob

    def curve(name,pts,material,r=.012):
        c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=12;c.bevel_depth=r;c.bevel_resolution=3
        sp=c.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
        for p,co in zip(sp.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
        ob=bpy.data.objects.new(name,c);COLL.objects.link(ob);c.materials.append(material);return ob

    def interp(controls,steps):
        out=[]
        for j in range(len(controls)-1):
            a=controls[max(j-1,0)];b=controls[j];c=controls[j+1];d=controls[min(j+2,len(controls)-1)]
            for k in range(steps):
                t=k/steps
                out.append(tuple(.5*((2*b[i])+(-a[i]+c[i])*t+(2*a[i]-5*b[i]+4*c[i]-d[i])*t*t+(-a[i]+3*b[i]-3*c[i]+d[i])*t*t*t) for i in range(len(b))))
        return out+[controls[-1]]

    def tube(name,controls,material,sides=36,steps=8,fold=0,cap=True):
        # Swept elliptical sections form one continuous garment or organic part.
        rows=interp(controls,steps);verts=[];faces=[]
        for j,row in enumerate(rows):
            pos=Vector(row[:3]);rx,ry=max(row[3],.001),max(row[4],.001)
            tangent=Vector(rows[min(j+1,len(rows)-1)][:3])-Vector(rows[max(j-1,0)][:3]);tangent.normalize()
            ax=Vector((1,0,0));ax=(ax-tangent*ax.dot(tangent)).normalized()
            if ax.length < .1:ax=Vector((0,1,0)).cross(tangent).normalized()
            ay=tangent.cross(ax).normalized()
            u=j/(len(rows)-1)
            for k in range(sides):
                th=2*pi*k/sides
                w=1+fold*(sin(u*35+th*3)*.5+sin(u*57-th*2)*.3)*sin(pi*u)**.6
                v=pos+ax*(rx*cos(th)*w)+ay*(ry*sin(th)*w);verts.append(tuple(v))
        for j in range(len(rows)-1):
            for k in range(sides):
                a=j*sides+k;b=j*sides+(k+1)%sides;faces.append((a,b,b+sides,a+sides))
        if cap:faces += [tuple(reversed(range(sides))),tuple((len(rows)-1)*sides+k for k in range(sides))]
        return mesh(name,verts,faces,material)

    def rings(name,controls,material,n=80,steps=6,delta=None,open_angle=0,solid=0):
        # Rows are z, horizontal radius, front depth, rear depth, y centre.
        rows=interp(controls,steps);verts=[];faces=[];closed=open_angle==0;ns=n if closed else n+1
        for row in rows:
            z,rx,front,back,cy=row
            for k in range(ns):
                th=open_angle+(2*pi-2*open_angle)*k/n
                x=rx*sin(th);f=cos(th);y=cy-(front if f>=0 else back)*f
                if delta:y+=delta(x,y,z,th)
                verts.append((x,y,z))
        for j in range(len(rows)-1):
            for k in range(n if closed else ns-1):
                a=j*ns+k;b=j*ns+(k+1)%ns;faces.append((a,b,b+ns,a+ns))
        if closed:faces += [tuple(reversed(range(ns))),tuple((len(rows)-1)*ns+k for k in range(ns))]
        ob=mesh(name,verts,faces,material,1)
        if solid:
            s=ob.modifiers.new('Fabric thickness','SOLIDIFY');s.thickness=solid;s.offset=0
        return ob

    def applique(name,pts,material,r=.008):return curve(name,pts,material,r)

    group('01 • anatomy and sculpted face')
    tube('Neck • shaped base',[(0,.04,4.65,.19,.18),(0,.035,4.85,.20,.19),(0,.035,5.12,.22,.20)],skin,48,8)
    def face_sculpt(x,y,z,th):
        front=max(cos(th),0)**6
        cheek=-.040*exp(-((abs(x)-.31)/.16)**2-((z-5.48)/.19)**2)
        socket=.040*exp(-((abs(x)-.235)/.12)**2-((z-5.86)/.17)**2)
        muzzle=-.027*exp(-(x/.22)**2-((z-5.30)/.13)**2)
        return front*(cheek+socket+muzzle)
    head=rings('Head • jaw, cheeks, eye sockets and chin',[(4.99,.19,.19,.12,.02),(5.045,.30,.28,.19,.02),(5.16,.43,.37,.26,.02),(5.35,.49,.43,.33,.02),(5.57,.535,.43,.40,.025),(5.84,.53,.415,.43,.035),(6.06,.51,.40,.43,.04),(6.26,.455,.34,.39,.045),(6.42,.32,.24,.28,.04),(6.49,.055,.045,.045,.04)],skin,96,6,face_sculpt)
    for sign in (-1,1):
        sphere('Ear • outer rim',(.535*sign,.015,5.64),(.10,.10,.19),skin,rot=(0,sign*.1,0))
        sphere('Ear • recessed warm interior',(.580*sign,-.078,5.65),(.055,.027,.12),skin_shadow)
        curve('Ear • inner helix',[(sign*.57,-.100,5.75),(sign*.60,-.105,5.69),(sign*.585,-.105,5.59),(sign*.56,-.100,5.57)],skin,.014)
    # A narrow bridge flows into the rounded nose tip.
    tube('Nose • bridge and tip',[(0,-.397,5.98,.035,.030),(0,-.445,5.85,.046,.046),(0,-.50,5.70,.065,.057),(0,-.565,5.63,.088,.075),(0,-.53,5.575,.072,.045)],skin,40,6)
    for sign in (-1,1):
        sphere('Nose • ala',(.066*sign,-.50,5.59),(.052,.064,.038),skin)
        sphere('Nose • nostril',(.059*sign,-.552,5.574),(.022,.013,.009),skin_shadow)
    curve('Mouth • smiling lip line',[(-.165,-.395,5.365),(-.11,-.44,5.323),(0,-.466,5.31),(.11,-.44,5.33),(.17,-.388,5.38)],lip,.010)
    curve('Mouth • lower lip',[(-.105,-.441,5.30),(0,-.461,5.283),(.105,-.438,5.307)],skin_shadow,.014)

    for sign in (-1,1):
        cx=sign*.225;cz=5.855
        def eyeface(x,z):
            th=math.asin(max(-.99,min(.99,x/.53)))
            return .035-.415*cos(th)+face_sculpt(x,0,z,th)
        # An almond-shaped patch meets the eyelid at the actual facial surface.
        # This replaces the protruding eyeball spheres used in the first draft.
        vv=[];ff=[];ss=64;rr=13
        for j in range(rr):
            r=.002+.998*j/(rr-1)
            for k in range(ss):
                a=2*pi*k/ss;xx=cx+.162*r*cos(a);zz=cz+(.150 if sin(a)>0 else .112)*r*sin(a)
                yy=eyeface(xx,zz)-.008-.122*(1-r*r)
                vv.append((xx,yy,zz))
        for j in range(rr-1):
            for k in range(ss):a=j*ss+k;b=j*ss+(k+1)%ss;ff.append((a,a+ss,b+ss,b))
        mesh('Eye • fitted almond sclera',vv,ff,eye_white,1)
        # Gaze follows the three-quarter presentation camera.
        ix=cx+.018
        eyey=eyeface(ix,cz)-.131
        sphere('Eye • brown iris',(ix,eyey-.005,cz+.002),(.096,.015,.110),iris)
        sphere('Eye • amber iris',(ix,eyey-.017,cz+.000),(.070,.008,.086),iris_light)
        sphere('Eye • pupil',(ix+.007,eyey-.026,cz+.004),(.052,.007,.070),pupil)
        sphere('Eye • main catchlight',(ix-.022,eyey-.034,cz+.05),(.018,.004,.021),glint,seg=24,rings=16)
        sphere('Eye • small catchlight',(ix+.026,eyey-.032,cz-.035),(.007,.003,.009),glint,seg=20,rings=12)
        lidtop=[];lidbottom=[]
        for j in range(17):
            u=-1+2*j/16;rr=max(0,1-u*u)
            xx=cx+.163*u;zt=cz+.150*rr**.50;zb=cz-.112*rr**.50
            lidtop.append((xx,eyeface(xx,zt)-.014,zt))
            lidbottom.append((xx,eyeface(xx,zb)-.013,zb))
        curve('Eye • upper lid',lidtop,skin,.014)
        curve('Eye • lower lid',lidbottom,skin,.010)
        curve('Eye • fine upper lash',[(x,y-.008,z-.006) for x,y,z in lidtop],hair_dark,.0045)
        tube('Brow • tapered arch',[(cx-.16,-.375,6.035,.008,.008),(cx-.09,-.418,6.09,.030,.016),(cx+.03,-.428,6.10,.035,.018),(cx+.14,-.385,6.06,.012,.008)],hair_dark,20,8)

    group('02 • swept chestnut hair')
    # Scalp shell ends behind the hairline; fringe is a set of pointed swept locks.
    sphere('Hair • scalp base',(0,.065,6.14),(.51,.425,.35),hair)
    locks=[
        [(.26,-.15,6.34,.12,.09),(.05,-.38,6.35,.15,.10),(-.27,-.48,6.34,.16,.075),(-.53,-.45,6.39,.008,.006)],
        [(.21,-.13,6.36,.12,.09),(.05,-.36,6.31,.13,.08),(-.21,-.49,6.26,.12,.065),(-.50,-.46,6.30,.004,.004)],
        [(.40,-.04,6.29,.10,.09),(.32,-.35,6.28,.13,.08),(.12,-.45,6.23,.10,.06),(-.15,-.46,6.22,.004,.004)],
        [(-.04,.02,6.36,.12,.10),(-.31,-.25,6.37,.16,.095),(-.47,-.43,6.32,.13,.07),(-.59,-.41,6.35,.003,.003)],
        [(-.32,.05,6.30,.12,.10),(-.47,-.18,6.25,.12,.085),(-.50,-.34,6.10,.075,.06),(-.47,-.36,5.94,.004,.004)],
        [(.41,.02,6.26,.10,.09),(.48,-.19,6.13,.10,.07),(.45,-.30,5.99,.05,.045),(.42,-.30,5.91,.004,.004)],
        [(-.44,.13,6.20,.10,.07),(-.50,.12,6.05,.09,.05),(-.49,.07,5.87,.004,.003)],
        [(.44,.16,6.20,.10,.07),(.50,.15,6.05,.09,.05),(.49,.07,5.87,.004,.003)]
    ]
    for k,points in enumerate(locks):
        tube('Hair lock %02d • pointed sweep'%k,points,hair if k%3 else hair_hi,32,12)
        rows=interp(points,10)
        for strand in range(7):
            pts=[]
            for j,row in enumerate(rows[2:-2],start=2):
                tangent=(Vector(rows[j+1][:3])-Vector(rows[j-1][:3])).normalized()
                ax=Vector((1,0,0));ax=(ax-tangent*ax.dot(tangent)).normalized()
                if ax.length<.1:ax=Vector((0,1,0)).cross(tangent).normalized()
                ay=tangent.cross(ax).normalized();normal=Vector((.1,-1,.35)).normalized()
                a=math.atan2(normal.dot(ay),normal.dot(ax))+(strand-3)*.18
                pt=Vector(row[:3])+ax*(row[3]*cos(a)*1.012)+ay*(row[4]*sin(a)*1.012)
                pts.append(tuple(pt))
            curve('Hair • sculpted directional strand',pts,hair_dark if strand%2 else hair_hi,.0018)

    group('03 • backwards cap with open front')
    v=[];f=[];nr=28;nt=96
    for j in range(nr+1):
        t=j/nr
        for k in range(nt):
            a=2*pi*k/nt
            # Raise the front cutout so the swept fringe comes through the opening.
            limit=1.44-.30*max(cos(a),0)**10
            ph=.025+(limit-.025)*t
            v.append((.565*sin(ph)*sin(a),.05-.48*sin(ph)*cos(a),6.205+.52*cos(ph)))
    for j in range(nr):
        for k in range(nt):
            a=j*nt+k;b=j*nt+(k+1)%nt;f.append((a,a+nt,b+nt,b))
    cap=mesh('Cap • tailored dome with hair opening',v,f,purple,1)
    so=cap.modifiers.new('Cotton cap thickness','SOLIDIFY');so.thickness=.025
    for a in (0,pi/3,2*pi/3,pi,4*pi/3,5*pi/3):
        pts=[]
        for j in range(20):
            ph=.10+1.24*j/19;pts.append((.57*sin(ph)*sin(a),.05-.486*sin(ph)*cos(a),6.208+.525*cos(ph)))
        curve('Cap • six panel stitching',pts,purple_dark,.0045)
    sphere('Cap • top button',(0,.05,6.738),(.05,.05,.025),purple)
    # Curved rear brim, shaped as a flat solid surface rather than a block.
    v=[];f=[]
    for j in range(8):
        u=j/7
        for k in range(33):
            a=-pi/2+pi*k/32
            x=(.40+.12*u)*sin(a);y=.35+(.12+.53*u)*cos(a)
            z=6.225-.055*u+.045*sin(a)**2
            v.append((x,y,z))
    for j in range(7):
        for k in range(32):a=j*33+k;f.append((a,a+1,a+34,a+33))
    brim=mesh('Cap • curved backwards brim',v,f,purple,2)
    so=brim.modifiers.new('Brim thickness','SOLIDIFY');so.thickness=.035
    curve('Cap • front adjustment strap',[(-.25,-.407,6.28),(0,-.455,6.25),(.25,-.407,6.28)],purple,.043)
    for x in (-.14,-.07,0,.07,.14):sphere('Cap • adjustment hole',(x,-.496,6.26),(.012,.006,.012),purple_dark,seg=16,rings=12)

    group('04 • tailored jacket and undershirt')
    rings('T-shirt • continuous torso',[(3.10,.52,.29,.27,0),(3.35,.56,.31,.29,0),(4.06,.65,.32,.29,.015),(4.40,.62,.31,.27,.015),(4.59,.34,.25,.24,.015),(4.72,.20,.19,.18,.02)],shirt,80,6)
    def cloth_delta(x,y,z,th):
        return .012*sin(22*z+th*2)*sin(th)**2+.008*sin(z*32-th*3)
    jacket_profile=[(3.10,.565,.33,.29,.025),(3.16,.61,.35,.32,.02),(3.39,.65,.38,.34,.02),(3.80,.68,.40,.36,.02),(4.16,.74,.40,.35,.02),(4.42,.78,.37,.32,.02),(4.56,.61,.31,.28,.025),(4.68,.26,.23,.21,.025)]
    rings('Jacket • continuous open shell',jacket_profile,pink,100,7,cloth_delta,.17,.035)
    # Zipper tapes follow the open front edges; the middle stays open over the shirt.
    for sign in (-1,1):
        pts=[]
        for row in interp(jacket_profile,8):
            z,rx,front,back,cy=row;x=sign*rx*sin(.17);y=cy-front*cos(.17)-.015
            pts.append((x,y,z))
        curve('Jacket • dark zipper facing',pts,pink_inner,.020)
        curve('Jacket • silver zip rail',[(x,y-.015,z) for x,y,z in pts[:-2]],metal,.006)
        for i in range(25):
            z=3.19+i*.049;x=sign*(.105+.015*sin((z-3.2)*2))
            box('Jacket • individual zipper tooth',(x,-.384,z),(.019,.012,.012),metal,.003)
    box('Jacket • zipper pull',(.10,-.407,3.22),(.055,.022,.080),metal,.012)
    # Raised collar panels frame the neck with a darker inner lining.
    for sign in (-1,1):
        collar=[(sign*.10,-.25,4.62),(sign*.23,-.20,4.66),(sign*.28,-.02,4.66),(sign*.20,.17,4.64)]
        rows=interp(collar,8);vv=[];ff=[]
        for p in rows:
            for h in (0,.025,.175,.20):vv.append((p[0]+sign*.035*h/.20,p[1]-.035*h/.20,p[2]+h))
        for j in range(len(rows)-1):
            for k in range(3):a=j*4+k;ff.append((a,a+1,a+5,a+4))
        col=mesh('Jacket • tailored standing collar',vv,ff,pink,2)
        so=col.modifiers.new('Collar fabric thickness','SOLIDIFY');so.thickness=.032
        curve('Jacket • collar topstitch',[(p[0]+sign*.035,p[1]-.039,p[2]+.197) for p in rows],pink_edge,.0045)
    # Ribbed waistband and attached fabric ridges.
    rings('Jacket • ribbed hem',[(3.05,.58,.32,.29,.02),(3.08,.605,.34,.31,.02),(3.20,.61,.34,.31,.02),(3.22,.59,.33,.30,.02)],pink,88,4,None,.17,.022)
    for k in range(58):
        th=.20+(2*pi-.4)*k/57
        curve('Jacket • fine waistband ribs',[(.609*sin(th),.02-.344*cos(th),3.085),(.614*sin(th),.02-.348*cos(th),3.185)],pink_edge,.003)
    for sign in (-1,1):
        applique('Jacket • slanted pocket opening',[(sign*.32,-.347,3.57),(sign*.44,-.324,3.41),(sign*.49,-.30,3.31)],pink_inner,.016)
        applique('Jacket • pocket seam',[(sign*.29,-.358,3.58),(sign*.40,-.344,3.39),(sign*.48,-.317,3.28)],pink_edge,.0055)

    # Each sleeve is a single loft, with tapered radii and shallow elbow folds.
    tube('Jacket • parcel arm sleeve',[(-.54,.025,4.35,.18,.20),(-.76,-.005,4.28,.25,.25),(-.96,-.07,3.98,.22,.23),(-1.00,-.24,3.77,.19,.20),(-1.08,-.45,3.66,.155,.16)],pink,56,12,.045)
    tube('Jacket • pocket arm sleeve',[(.54,.025,4.35,.18,.20),(.78,.015,4.25,.25,.26),(1.00,-.025,3.91,.235,.24),(.93,-.17,3.62,.20,.21),(.73,-.35,3.36,.155,.16)],pink,56,12,.055)
    for name,a,b in [('parcel',(-1.05,-.40,3.68),(-1.12,-.53,3.64)),('pocket',(.77,-.31,3.41),(.70,-.38,3.30))]:
        tube('Jacket • '+name+' ribbed cuff',[(*a,.16,.16),(*b,.155,.15)],pink,44,8)
    box('Jacket • sleeve utility pocket',(.985,-.115,4.10),(.10,.24,.27),pink,.033,rot=(0,-.13,-.06))
    box('Jacket • sleeve pocket flap',(.995,-.13,4.22),(.12,.25,.07),pink_edge,.022)
    sphere('Jacket • sleeve pocket snap',(1.064,-.14,4.20),(.012,.018,.018),metal,seg=20,rings=12)
    for sign in (-1,1):
        curve('Jacket • shoulder stitching',[(sign*.40,-.27,4.52),(sign*.65,-.29,4.43),(sign*.77,-.20,4.28)],pink_edge,.005)

    group('05 • cargo trousers with connected silhouette')
    pieces=[]
    pieces.append(rings('Pants • pelvis volume',[(2.62,.18,.22,.22,.025),(2.78,.43,.28,.30,.025),(2.98,.56,.31,.32,.025),(3.17,.55,.30,.29,.025)],pants,72,7))
    leg_controls={
        'left':[(-.265,.03,2.94,.285,.30),(-.29,.02,2.62,.28,.30),(-.30,-.055,2.23,.26,.28),(-.30,-.11,1.84,.235,.25),(-.29,-.06,1.50,.23,.23),(-.30,.00,1.05,.205,.205),(-.30,.025,.67,.175,.18),(-.30,.025,.54,.155,.16)],
        'right':[(.265,.035,2.94,.285,.30),(.29,.02,2.62,.28,.30),(.33,.005,2.23,.26,.28),(.36,-.015,1.84,.235,.25),(.40,-.055,1.48,.225,.23),(.43,-.065,1.04,.195,.205),(.46,-.06,.67,.17,.175),(.46,-.06,.54,.155,.16)]}
    for name,points in leg_controls.items():pieces.append(tube('Pants • '+name+' baggy leg',points,pants,60,10,.05))
    # Merge the overlapping pelvis/legs into a continuous high-resolution surface.
    verts=[];faces=[]
    for p in pieces:
        dep=bpy.context.evaluated_depsgraph_get();ev=p.evaluated_get(dep);me=ev.to_mesh();offset=len(verts)
        verts.extend(tuple(p.matrix_world @ v.co) for v in me.vertices)
        faces.extend(tuple(offset+i for i in face.vertices) for face in me.polygons)
        ev.to_mesh_clear();bpy.data.objects.remove(p,do_unlink=True)
    trousers=mesh('Trousers • unified cargo silhouette',verts,faces,pants)
    rem=trousers.modifiers.new('Seamless sculpted trouser surface','REMESH');rem.mode='VOXEL';rem.voxel_size=.018;rem.use_smooth_shade=True
    sm=trousers.modifiers.new('Gentle fabric smoothing','SMOOTH');sm.factor=.45;sm.iterations=3
    for sign,cx,cy in [(-1,-.30,.025),(1,.46,-.06)]:
        tube('Trousers • ankle cuff',[(cx,cy,.51,.155,.16),(cx,cy,.64,.17,.175)],pants,40,8)
        for k in range(22):
            a=2*pi*k/22
            curve('Trousers • cuff rib',[(cx+.166*cos(a),cy+.171*sin(a),.53),(cx+.171*cos(a),cy+.176*sin(a),.62)],pants_edge,.0024)
    # Cargo pockets sit on the outer thigh; the flaps and double stitching are separate.
    for sign in (-1,1):
        x=sign*.535
        box('Cargo • outer thigh pocket',(x,-.045,2.27),(.12,.37,.43),pants,.043,rot=(0,sign*.04,0))
        box('Cargo • pocket flap',(x+sign*.026,-.05,2.47),(.125,.39,.11),pants,.025)
        curve('Cargo • flap topstitch',[(x+sign*.073,-.22,2.485),(x+sign*.078,-.05,2.49),(x+sign*.073,.13,2.485)],pants_edge,.004)
        sphere('Cargo • flap snap',(x+sign*.09,-.05,2.445),(.011,.022,.022),purple_dark,seg=16,rings=12)
    for name,points in leg_controls.items():
        sign=-1 if name=='left' else 1
        pts=[(p[0]+sign*p[3]*.82,p[1]-p[4]*.57,p[2]) for p in points[1:-1]]
        curve('Trousers • side seam',pts,pants_seam,.005)
        curve('Trousers • twin needle stitch',[(x-sign*.013,y-.004,z) for x,y,z in pts],pants_edge,.0026)

    group('06 • trainers with layered soles and laces')
    def shoe(name,cx,cy,angle):
        ca,sa=cos(angle),sin(angle)
        def t(p):x,y,z=p;return (cx+x*ca-y*sa,cy+x*sa+y*ca,z)
        # Rounded outsole contour, toe wider than the heel.
        contour=[]
        for k in range(80):
            a=2*pi*k/80
            y=-.12+.46*cos(a);w=.22 if cos(a)<0 else .185
            x=w*sin(a);contour.append((x,y))
        v=[];f=[]
        for z,sc in [(.025,.91),(.045,1),(.12,1.035),(.185,1),(.205,.94)]:
            for x,y in contour:v.append(t((x*sc,y*sc,z)))
        for j in range(4):
            for k in range(80):a=j*80+k;b=j*80+(k+1)%80;f.append((a,a+80,b+80,b))
        f.extend([tuple(range(80)),tuple(320+k for k in reversed(range(80)))]);mesh('Trainer '+name+' • sculpted outsole',v,f,sole,1)
        rows=[(-.58,.035,.225,.025),(-.53,.16,.25,.065),(-.43,.215,.26,.09),(-.28,.22,.28,.11),(-.12,.205,.32,.145),(.035,.19,.35,.18),(.19,.175,.335,.17),(.29,.12,.29,.10),(.32,.025,.27,.025)]
        vv=[];ff=[];ss=56
        for y,rx,z,rz in interp(rows,6):
            for k in range(ss):
                a=2*pi*k/ss;vv.append(t((rx*cos(a),y,z+rz*sin(a))))
        rr=len(vv)//ss
        for j in range(rr-1):
            for k in range(ss):a=j*ss+k;b=j*ss+(k+1)%ss;ff.append((a,a+ss,b+ss,b))
        ff.extend([tuple(range(ss)),tuple((rr-1)*ss+k for k in reversed(range(ss)))])
        mesh('Trainer '+name+' • continuous shaped upper',vv,ff,shoes,1)
        tongue=box('Trainer '+name+' • padded tongue',t((0,-.045,.50)),(.19,.30,.05),shoe_panel,.045,rot=(.10,0,angle))
        for side in (-1,1):
            curve('Trainer '+name+' • suede side panel',[t((side*.19,.21,.28)),t((side*.20,.02,.31)),t((side*.207,-.22,.30)),t((side*.18,-.43,.26))],shoe_panel,.022)
            curve('Trainer '+name+' • toe stitching',[t((side*.15,-.48,.30)),t((side*.20,-.38,.335)),t((side*.19,-.25,.355))],sole,.003)
        for j in range(6):
            y=-.28+j*.064;z=.39+j*.023
            for side in (-1,1):sphere('Trainer '+name+' • eyelet',t((side*.113,y,z)),(.019,.015,.009),webbing,seg=16,rings=12)
            curve('Trainer '+name+' • crossed lace',[t((-.11,y,z+.008)),t((0,y+.018,z+.027)),t((.11,y+.046,z+.025))],lace,.009)
            curve('Trainer '+name+' • crossed lace',[t((.11,y,z+.008)),t((0,y+.018,z+.032)),t((-.11,y+.046,z+.025))],lace,.009)
        box('Trainer '+name+' • heel pull tab',t((0,.255,.47)),(.10,.05,.14),purple,.018,rot=(0,0,angle))
        box('Trainer '+name+' • tongue patch',t((0,.015,.55)),(.095,.08,.012),purple,.015,rot=(0,0,angle))
        tube('Sock '+name,[(cx,cy,.43,.14,.15),(cx,cy,.59,.145,.15)],shirt,36,6)
    shoe('left',-.30,.025,-.07);shoe('right',.46,-.06,.10)

    group('07 • delivery backpack and webbing')
    box('Backpack • main padded body',(0,.58,3.91),(1.17,.62,1.70),cyan,.145)
    box('Backpack • rear padded panel',(0,.245,3.96),(.98,.10,1.45),teal,.12)
    box('Backpack • top foldover flap',(0,.935,4.49),(1.05,.10,.38),lime,.065)
    box('Backpack • flap cyan bound edge',(0,.996,4.32),(1.03,.024,.035),teal,.012)
    box('Backpack • front utility pocket',(0,.956,3.57),(.80,.17,.56),cyan,.075)
    box('Backpack • pocket lime flap',(0,1.058,3.83),(.81,.07,.16),lime,.035)
    box('Backpack • small reflective badge',(0,1.054,3.55),(.21,.018,.15),shirt,.018)
    for sign in (-1,1):
        x=sign*.63
        box('Backpack • side gusset pocket',(x,.64,3.53),(.18,.43,.56),cyan,.065)
        box('Backpack • side pocket lid',(x,.64,3.81),(.19,.44,.12),lime,.025)
        curve('Backpack • side pocket topstitch',[(x+sign*.095,.45,3.75),(x+sign*.102,.44,3.32),(x+sign*.102,.83,3.32),(x+sign*.095,.84,3.75)],teal,.008)
        curve('Backpack • long outer piping',[(sign*.49,.91,3.15),(sign*.57,.88,3.24),(sign*.57,.88,4.58),(sign*.48,.89,4.69)],teal,.014)
        # Flexible broad straps wrap over the shoulder and down the front of the jacket.
        centres=[(sign*.39,.37,4.60),(sign*.43,.06,4.67),(sign*.45,-.25,4.49),(sign*.43,-.44,4.24),(sign*.40,-.455,3.94),(sign*.38,-.43,3.67)]
        cc=interp(centres,7);vv=[];ff=[]
        for p in cc:vv.extend([(p[0]-.072,p[1],p[2]),(p[0]+.072,p[1],p[2])])
        for j in range(len(cc)-1):a=j*2;ff.append((a,a+1,a+3,a+2))
        strap=mesh('Backpack • curved shoulder strap',vv,ff,webbing,1);so=strap.modifiers.new('Webbing thickness','SOLIDIFY');so.thickness=.035
        for dx in (-.057,.057):curve('Backpack • strap edge stitching',[(p[0]+dx,p[1]-.012,p[2]) for p in cc],cyan,.004)
        # Open rectangular buckles: four lime bars around the dark strap.
        bx=sign*.415;by=-.493;bz=4.16
        for dx in (-.086,.086):box('Backpack • lime buckle side',(bx+dx,by,bz),(.036,.038,.18),lime,.012)
        for dz in (-.073,.073):box('Backpack • lime buckle crossbar',(bx,by,bz+dz),(.19,.038,.034),lime,.012)
        curve('Backpack • loose webbing tail',[(sign*.39,-.46,3.99),(sign*.40,-.48,3.77),(sign*.34,-.48,3.60)],webbing,.029)
    curve('Backpack • carry handle',[(-.17,.56,4.76),(-.13,.56,4.90),(.13,.56,4.90),(.17,.56,4.76)],webbing,.031)

    group('08 • hands and held parcel')
    # Supporting hand curls around the outer left corner of the parcel.
    tube('Hand • parcel wrist',[(-1.10,-.48,3.65,.105,.10),(-1.23,-.73,3.71,.11,.10),(-1.28,-.84,3.77,.11,.12)],skin,40,8)
    sphere('Hand • parcel palm',(-1.28,-.87,3.77),(.11,.10,.20),skin)
    for j in range(4):
        z=3.63+j*.094
        tube('Hand • curled finger %d'%j,[(-1.32,-.89,z,.042,.039),(-1.29,-1.015,z+.015,.043,.038),(-1.15,-1.04,z+.018,.037,.031),(-1.08,-1.015,z+.019,.025,.023)],skin,24,7)
        sphere('Hand • finger nail',(-1.10,-1.043,z+.030),(.033,.008,.021),skin_shadow,seg=20,rings=12)
    tube('Hand • parcel thumb',[(-1.28,-.80,3.88,.06,.06),(-1.27,-.91,3.98,.055,.05),(-1.15,-.98,3.98,.04,.035)],skin,28,7)
    # Other hand enters the jacket pocket; only back of hand and thumb remain visible.
    tube('Hand • pocket wrist',[(.70,-.36,3.33,.10,.10),(.61,-.37,3.21,.10,.10),(.53,-.35,3.15,.08,.08)],skin,36,8)
    tube('Hand • pocket thumb',[(.66,-.43,3.32,.045,.04),(.62,-.46,3.24,.043,.037),(.57,-.43,3.18,.025,.025)],skin,24,7)
    # Crisp cardboard panels and a single strip of tape, rather than a rounded suitcase.
    parcel=box('Parcel • held kraft box',(-.94,-.745,3.87),(.65,.57,.76),cardboard,.012,rot=(0,-.04,-.025))
    box('Parcel • centre tape front',(-.94,-1.036,3.87),(.105,.009,.76),tape,.003,rot=(0,-.04,-.025))
    box('Parcel • centre tape top',(-.94,-.745,4.254),(.105,.57,.010),tape,.002,rot=(0,-.04,-.025))
    curve('Parcel • top folding seam',[(-1.25,-.745,4.259),(-.95,-.745,4.261),(-.62,-.745,4.259)],cardboard_edge,.003)
    curve('Parcel • front side edge',[(-1.263,-1.037,3.50),(-1.263,-1.037,4.24)],cardboard_edge,.0025)

    group('09 • studio')
    box('Ground',(0,0,-.065),(200,200,.10),floor,.0)
    # An actual curved studio wall gives a seamless light backdrop in the render.
    vv=[];ff=[];profile=[(-20,-.010),(3,-.010)]
    for j in range(1,65):
        a=-pi/2+(pi/2)*j/64;profile.append((3+2*cos(a),1.99+2*sin(a)))
    profile.extend([(5,5),(5,10)])
    for y,z in profile:vv.extend([(-20,y,z),(20,y,z)])
    for j in range(len(profile)-1):a=j*2;ff.append((a,a+1,a+3,a+2))
    mesh('Studio • curved cyclorama',vv,ff,floor,1)
    world=bpy.data.worlds.new('Light studio environment');world.use_nodes=True;world.node_tree.nodes['Background'].inputs['Color'].default_value=(*rgb('ECE9E6'),1);world.node_tree.nodes['Background'].inputs['Strength'].default_value=.25;scene.world=world
    def light(name,pos,power,size):
        bpy.ops.object.light_add(type='AREA',location=pos);ob=link_obj(bpy.context.object);ob.name=name;ob.data.energy=power;ob.data.shape='DISK';ob.data.size=size
        ob.rotation_euler=(Vector((0,0,3.5))-ob.location).to_track_quat('-Z','Y').to_euler()
    light('Key • large warm softbox',(-4,-6,9),1500,5)
    light('Fill • face and jacket',(5,-4,6),800,4)
    light('Rim • hair and cyan backpack',(2,4,8),1300,4)
    bpy.ops.object.camera_add(location=(8,-16,7.0));cam=link_obj(bpy.context.object);cam.name='Camera • reference three-quarter view'
    cam.rotation_euler=(Vector((-.08,-.02,3.44))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=7.70;cam.data.lens=80;scene.camera=cam
    scene.render.resolution_x=1120;scene.render.resolution_y=1500;scene.render.resolution_percentage=100
    scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
    scene.render.engine='CYCLES'
    scene.cycles.device='CPU';scene.cycles.samples=48;scene.cycles.use_denoising=True
    if hasattr(scene,'eevee'):
        ee=scene.eevee
        if hasattr(ee,'use_gtao'):ee.use_gtao=True;ee.gtao_distance=3;ee.gtao_factor=1.1
        if hasattr(ee,'taa_render_samples'):ee.taa_render_samples=128
    for transform in ('AgX','Filmic','Standard'):
        try:
            scene.view_settings.view_transform=transform
            break
        except TypeError:pass
    for look in ('AgX - Medium High Contrast','Medium High Contrast','None'):
        try:
            scene.view_settings.look=look
            break
        except TypeError:pass
    scene.view_settings.exposure=0;scene.view_settings.gamma=1
    scene.render.filepath=os.path.join(OUT,'ParcelPanicCourier_Rebuild_Preview.png')

    refcol=group('10 • packed source reference — viewport only')
    pic=bpy.data.images.load(REFERENCE,check_existing=True);pic.pack()
    ref=bpy.data.objects.new('Original concept image • compare proportions',None);ref.empty_display_type='IMAGE';ref.data=pic;ref.empty_display_size=6.7;ref.location=(-4.1,1.2,3.4);ref.rotation_euler=(pi/2,0,0);ref.hide_render=True;refcol.objects.link(ref)
    refcol.hide_render=True
    # On opening, the camera view presents the actual model with its materials.
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':
                space=area.spaces.active;space.shading.type='MATERIAL';space.region_3d.view_perspective='CAMERA'
    for obj in scene.objects:obj.select_set(False)
    bpy.context.view_layer.objects.active=None
    scene['Description']='Editable geometry rebuilt from supplied courier image. Static concept study, not animation-ready.'
    scene['Source reference']=REFERENCE
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,'ParcelPanicCourier_Rebuild.blend'))
    bpy.ops.render.render(write_still=True)
    report={'blend':bpy.data.filepath,'render':scene.render.filepath,'objects':len(scene.objects),'mesh_vertices':sum(len(o.data.vertices) for o in scene.objects if o.type=='MESH')}
    with open(os.path.join(OUT,'rebuild_report.json'),'w') as f:json.dump(report,f,indent=2)
    print('COURIER_REBUILD_FINISHED',report)

try:
    build()
except Exception:
    with open('/private/tmp/courier_rebuild_error.txt','w') as f:f.write(traceback.format_exc())
    raise
