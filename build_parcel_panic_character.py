"""Build an editable, stylised 3D Parcel Panic courier inspired by the reference."""
import bpy, math, os
from mathutils import Vector

OUT = "/Users/joyhowlader/Documents/ChatGPT/final year project/Game/Assets/Characters/ParcelPanicCourier"
os.makedirs(OUT, exist_ok=True)

# Start a clean, separate character scene.
for old in list(bpy.data.objects):
    bpy.data.objects.remove(old, do_unlink=True)

def material(name, rgb, rough=.58, metallic=0):
    m=bpy.data.materials.new(name); m.diffuse_color=(*rgb,1); m.roughness=rough; m.metallic=metallic
    m.use_nodes=True
    bsdf=m.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value=(*rgb,1)
        bsdf.inputs["Roughness"].default_value=rough
        bsdf.inputs["Metallic"].default_value=metallic
    return m

skin=material("Skin | warm peach",(.78,.43,.27))
skinlight=material("Skin | warm highlights",(.93,.63,.43))
hair=material("Hair | deep chestnut",(.16,.065,.035))
hairhi=material("Hair | warm chestnut highlights",(.28,.12,.055))
purple=material("Cap and trousers | bright purple",(.29,.12,.72))
purpledark=material("Cap and trouser shadow",(.16,.07,.39))
pink=material("Courier jacket | vivid pink",(.94,.08,.43))
pinklight=material("Jacket seams | pale pink",(1,.32,.59))
cyan=material("Delivery backpack | cyan",(.015,.65,.81))
cyandark=material("Backpack panels | deep teal",(.01,.33,.47))
lime=material("Lime green accents",(.69,.91,.08))
navy=material("Shoes and straps | navy",(.035,.055,.13))
sole=material("Sneaker soles | warm white",(.91,.88,.78))
white=material("Eye whites",(.98,.96,.89))
iris=material("Brown irises",(.27,.11,.035))
black=material("Pupils and details",(.025,.015,.02))
card=material("Parcel | kraft cardboard",(.62,.34,.14))
tape=material("Parcel | pale tape",(.93,.73,.42))
label=material("Parcel | label",(.98,.92,.76))
metal=material("Zip and buckle metal",(.67,.72,.75),.34,.35)

def finish(o,name,mat,smooth=False):
    o.name=name
    if mat:o.data.materials.append(mat)
    if smooth and o.type=='MESH':
        for p in o.data.polygons:p.use_smooth=True
    return o

def ball(name,loc,scale,mat,rot=None,seg=40,rings=28):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg,ring_count=rings,radius=1,location=loc)
    o=bpy.context.object;o.scale=scale
    if rot:o.rotation_euler=rot
    return finish(o,name,mat,True)

def box(name,loc,scale,mat,bevel=.07,rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=bpy.context.object;o.dimensions=scale
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rot:o.rotation_euler=rot
    finish(o,name,mat)
    if bevel:
        b=o.modifiers.new("Rounded tailored edges",'BEVEL');b.width=bevel;b.segments=4
        o.modifiers.new("Soft corner normals",'WEIGHTED_NORMAL')
    return o

def rod(name,a,b,r,mat,vertices=32):
    a,b=Vector(a),Vector(b);d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=d.length,location=(a+b)*.5)
    o=bpy.context.object;o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y')
    return finish(o,name,mat,True)

def path(name,pts,mat,r=.012):
    c=bpy.data.curves.new(name,'CURVE');c.dimensions='3D';c.resolution_u=16;c.bevel_depth=r;c.bevel_resolution=3
    s=c.splines.new('BEZIER');s.bezier_points.add(len(pts)-1)
    for p,co in zip(s.bezier_points,pts):p.co=co;p.handle_left_type='AUTO';p.handle_right_type='AUTO'
    o=bpy.data.objects.new(name,c);bpy.context.collection.objects.link(o);o.data.materials.append(mat);return o

def segment(name,a,b,width,depth,mat):
    a,b=Vector(a),Vector(b);d=b-a
    o=ball(name,(a+b)*.5,(width,depth,d.length*.62),mat,seg=40,rings=28)
    o.rotation_mode='QUATERNION';o.rotation_quaternion=d.to_track_quat('Z','Y')
    return o

# Coordinates: character faces +Y.  Feet stand on Z=0.
# Bag is behind the torso and intentionally visible in the front three-quarter view.
box("Backpack | structured cyan body",(0,-.37,1.91),(.82,.42,.92),cyan,.16)
box("Backpack | padded rear panel",(0,-.594,1.90),(.66,.045,.76),cyandark,.11)
box("Backpack | large top flap",(0,-.63,2.23),(.72,.09,.25),lime,.07)
box("Backpack | flap edge",(0,-.682,2.12),(.61,.025,.045),cyan,.018)
box("Backpack | front pocket",(-.02,-.65,1.70),(.53,.12,.34),cyan,.08)
box("Backpack | pocket flap",(-.02,-.727,1.84),(.52,.045,.12),lime,.04)
box("Backpack | side pocket",(-.43,-.39,1.69),(.17,.34,.37),cyandark,.06)
box("Backpack | side pocket flap",(-.43,-.40,1.88),(.18,.34,.09),cyan,.035)
for x in (-.27,.27):
    segment("Backpack | shoulder strap",(x,-.22,2.25),(x*.88,.12,1.45),.09,.06,navy)
    box("Backpack | lime strap adjuster",(x*.93,-.01,1.84),(.16,.07,.10),lime,.025)
    box("Backpack | strap slider",(x*.93,-.01,1.84),(.055,.076,.12),navy,.016)
box("Backpack | brand badge",(0,-.803,1.71),(.19,.025,.11),label,.025)

# Body: softly rounded jacket with a visible waist and high collar.
ball("Jacket | torso",(0,.015,1.87),(.48,.30,.67),pink)
ball("Jacket | hem",(0,.015,1.39),(.48,.30,.13),pinklight)
ball("T-shirt | neckline",(0,.21,2.31),(.22,.06,.22),white)
box("Jacket | front zipper",(0,.310,1.91),(.025,.025,.82),metal,.01)
box("Jacket | zipper pull",(0,.329,1.54),(.06,.024,.075),lime,.015)
box("Jacket | left front panel",(-.11,.296,1.91),(.20,.025,.72),pink,.025)
box("Jacket | right front panel",(.11,.296,1.91),(.20,.025,.72),pink,.025)
for x in (-.31,.31):
    box("Jacket | chest pocket",(x,.289,2.13),(.17,.04,.16),pinklight,.025)
    box("Jacket | pocket flap",(x,.319,2.20),(.18,.035,.055),pink,.015)
    box("Jacket | pocket snap",(x,.344,2.19),(.025,.012,.022),metal,.009)
box("Jacket | left collar",(-.16,.23,2.44),(.22,.17,.19),pinklight,.065,(0,0,math.radians(-15)))
box("Jacket | right collar",(.16,.23,2.44),(.22,.17,.19),pinklight,.065,(0,0,math.radians(15)))
for z in (1.49,1.54):
    path("Jacket | ribbed hem stitch",[(-.37,.20,z),(0,.30,z),(.37,.20,z)],pink,.008)

# Pants: relaxed cargo fit with slight bends in the knees and ankle cuffs.
ball("Trousers | hips",(0,-.005,1.25),(.43,.29,.30),purple)
segment("Trousers | left thigh",(-.22,0,1.19),(-.29,.10,.73),.205,.25,purple)
segment("Trousers | left shin",(-.29,.10,.72),(-.34,.22,.20),.14,.19,purple)
segment("Trousers | right thigh",(.22,-.015,1.19),(.31,-.08,.74),.20,.25,purple)
segment("Trousers | right shin",(.31,-.08,.73),(.39,.10,.20),.14,.19,purple)
for x,y,z in ((-.34,.22,.18),(.39,.10,.18)):
    ball("Trousers | ankle cuff",(x,y,z),(.16,.19,.10),purpledark)
box("Cargo pocket | left",(-.40,.055,.79),(.13,.09,.24),purpledark,.035,(0,0,math.radians(-5)))
box("Cargo pocket | left flap",(-.40,.108,.90),(.14,.035,.07),purple,.018)
box("Cargo pocket | right",(.48,-.03,.84),(.13,.10,.23),purpledark,.035,(0,0,math.radians(6)))
box("Cargo pocket | right flap",(.48,.026,.95),(.14,.035,.07),purple,.018)
path("Trouser seam | left",[(-.26,.238,1.12),(-.30,.282,.84),(-.34,.29,.42)],purpledark,.012)
path("Trouser seam | right",[(.24,.224,1.12),(.31,.19,.84),(.39,.265,.42)],purpledark,.012)

# High-top trainers, with a thick pale sole, raised tongue and visible laces.
def sneaker(side,x,y):
    box(f"Trainer {side} | sole",(x,y+.04,.09),(.39,.58,.15),sole,.07)
    box(f"Trainer {side} | upper",(x,y+.075,.20),(.35,.49,.22),navy,.09)
    ball(f"Trainer {side} | toe cap",(x,y+.27,.22),(.18,.18,.12),navy)
    box(f"Trainer {side} | tongue",(x,y+.02,.32),(.16,.23,.08),cyandark,.04)
    for i in range(4):
        yy=y-.07+i*.075
        path(f"Trainer {side} | lace {i}",[(x-.075,yy,.34),(x,yy+.025,.37),(x+.075,yy,.34)],label,.014)
    box(f"Trainer {side} | heel tab",(x,y-.19,.28),(.09,.06,.10),purple,.02)
sneaker("left",-.34,.22)
sneaker("right",.39,.10)

# Arms: left arm bends forward to support the parcel; right hand rests at the hip.
segment("Jacket | left sleeve",(-.38,.00,2.27),(-.55,.18,1.91),.17,.20,pink)
ball("Jacket | left elbow",(-.55,.18,1.91),(.16,.17,.16),pink)
segment("Jacket | left forearm",(-.55,.18,1.91),(-.46,.43,1.72),.13,.15,pink)
box("Jacket | left cuff",(-.46,.43,1.72),(.25,.19,.12),pinklight,.045,(0,0,math.radians(-20)))
ball("Hand | supporting parcel",(-.43,.53,1.65),(.12,.13,.14),skin)

segment("Jacket | right sleeve",(.38,.00,2.27),(.56,.05,1.94),.17,.20,pink)
ball("Jacket | right elbow",(.56,.05,1.94),(.16,.17,.16),pink)
segment("Jacket | right forearm",(.56,.05,1.94),(.47,.27,1.75),.13,.15,pink)
box("Jacket | right cuff",(.47,.27,1.75),(.25,.18,.12),pinklight,.04,(0,0,math.radians(18)))
ball("Hand | at hip",(.45,.33,1.68),(.12,.12,.14),skin)
box("Parcel | box",(.39,.68,1.68),(.40,.38,.43),card,.055,(0,0,math.radians(7)))
box("Parcel | top tape",(.39,.68,1.903),(.10,.39,.018),tape,.008,(0,0,math.radians(7)))
box("Parcel | cross tape",(.39,.68,1.68),(.405,.08,.44),tape,.008,(0,0,math.radians(7)))
box("Parcel | shipping label",(.39,.879,1.73),(.17,.018,.12),label,.012,(0,0,math.radians(7)))

# Head, neck and face. The face looks forward along +Y.
ball("Neck",(0,.035,2.48),(.19,.19,.22),skin)
ball("Head",(0,.07,2.89),(.43,.37,.49),skin)
ball("Ear | left",(-.425,.07,2.86),(.11,.12,.16),skin)
ball("Ear | right",(.425,.07,2.86),(.11,.12,.16),skin)
ball("Ear inner | left",(-.455,.155,2.86),(.047,.025,.078),skinlight)
ball("Ear inner | right",(.455,.155,2.86),(.047,.025,.078),skinlight)
ball("Nose",(0,.424,2.83),(.075,.07,.09),skinlight)
for x in (-.16,.16):
    ball("Eye | white",(x,.390,2.96),(.108,.052,.125),white)
    ball("Eye | iris",(x+.018,.437,2.96),(.058,.028,.072),iris)
    ball("Eye | pupil",(x+.024,.459,2.96),(.030,.016,.043),black)
    ball("Eye | glint",(x+.005,.473,2.99),(.014,.009,.017),white,seg=24,rings=16)
    path("Eyebrow",[(x-.09,.40,3.13),(x,.43,3.16),(x+.09,.40,3.13)],hair,.025)
path("Friendly smile",[(-.12,.406,2.72),(-.06,.443,2.685),(0,.45,2.68),(.06,.443,2.685),(.12,.406,2.72)],hair,.012)

# Swept hair: cap leaves a visible front fringe and several soft sculpted locks.
ball("Hair | base",(0,.005,3.12),(.40,.34,.25),hair)
for i,(x,y,z,sx,sy,sz,ang) in enumerate((
    (-.28,.22,3.17,.22,.20,.12,-25),(-.18,.31,3.20,.23,.17,.13,-15),
    (-.04,.34,3.18,.23,.16,.12,8),(.12,.30,3.15,.20,.17,.12,22),
    (-.31,-.10,3.14,.18,.22,.12,-32),(.26,-.13,3.14,.16,.21,.11,25))):
    ball("Hair | sculpted lock %02d"%i,(x,y,z),(sx,sy,sz),hairhi if i%2 else hair,(0,0,math.radians(ang)))
for x in (-.24,-.12,0,.12):
    path("Hair | fine strand",[(x,.37,3.15),(x+.035,.42,3.11),(x+.06,.415,3.05)],hairhi,.009)

# Backwards purple baseball cap, with stitched panels and lime adjuster detail.
ball("Cap | crown",(0,-.025,3.28),(.45,.40,.22),purple)
box("Cap | brim pointing backwards",(0,-.34,3.23),(.54,.45,.075),purpledark,.035)
box("Cap | rear adjuster",(0,.335,3.24),(.20,.035,.08),lime,.02)
path("Cap | panel seam",[(0,-.24,3.47),(0,.02,3.50),(0,.24,3.42)],pinklight,.009)
box("Cap | side badge",(-.34,.005,3.30),(.04,.15,.09),lime,.018)

# Small stylistic details: seams, zipper teeth, jacket piping, backpack stitching.
for z in [1.61+i*.035 for i in range(5)]:
    ball("Zip teeth",(0,.333,z),(.012,.009,.009),sole,seg=16,rings=12)
path("Jacket | left piping",[(-.29,.29,2.25),(-.36,.26,1.90),(-.30,.26,1.56)],pinklight,.009)
path("Jacket | right piping",[(.29,.29,2.25),(.36,.26,1.90),(.30,.26,1.56)],pinklight,.009)
for x in (-.26,.26):
    path("Backpack | seam piping",[(x,-.69,1.57),(x,-.70,1.92),(x,-.68,2.27)],cyandark,.012)

# Studio floor, camera and soft lighting.
floor_mat=material("Studio backdrop | soft lavender grey",(.82,.82,.88),.82)
box("Studio floor",(0,0,-.08),(200,200,.12),floor_mat,0)
world=bpy.data.worlds.new("Soft studio world") if not bpy.data.worlds else bpy.data.worlds[0]
bpy.context.scene.world=world;world.color=(.72,.72,.72)
def area(name,loc,power,size):
    bpy.ops.object.light_add(type='AREA',location=loc);o=bpy.context.object;o.name=name;o.data.energy=power;o.data.shape='DISK';o.data.size=size
    o.rotation_euler=(Vector((0,0,1.8))-o.location).to_track_quat('-Z','Y').to_euler()
area("Key softbox",(4,5,6),500,4.5)
area("Fill softbox",(-4,3,3.8),320,4)
area("Back rim light",(0,-4,5),480,3)
bpy.ops.object.camera_add(location=(-4.6,7.3,3.35));cam=bpy.context.object;cam.name="Courier | front three-quarter camera"
cam.rotation_euler=(Vector((0,.08,1.75))-cam.location).to_track_quat('-Z','Y').to_euler();cam.data.type='ORTHO';cam.data.ortho_scale=4.35
scene=bpy.context.scene;scene.camera=cam;scene.render.engine='BLENDER_EEVEE'
scene.render.resolution_x=1200;scene.render.resolution_y=1600;scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG';scene.render.film_transparent=False
scene.view_settings.view_transform='Standard';scene.view_settings.look='Medium High Contrast'
scene.render.filepath=os.path.join(OUT,"ParcelPanicCourier_Concept_Render.png")

# Select the character parts, leaving stage/camera/lights unselected for easy study.
for o in scene.objects:
    o.select_set(False)
    if o.type=='MESH' and o.name not in {"Studio floor"}:
        o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects.get("Jacket | torso")
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"ParcelPanicCourier_Concept.blend"))
bpy.ops.render.render(write_still=True)
print("Created editable courier concept and render in",OUT)
