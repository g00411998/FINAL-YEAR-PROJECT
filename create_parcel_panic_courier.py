import bpy, math, os
from mathutils import Vector

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Game", "Assets", "Characters", "ParcelPanicCourier")
os.makedirs(OUT, exist_ok=True)

# Start with an empty scene.
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
for datablocks in (bpy.data.materials, bpy.data.curves, bpy.data.meshes, bpy.data.cameras, bpy.data.lights):
    pass

def mat(name, color, roughness=0.78):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color, 1)
    m.roughness = roughness
    return m

purple = mat("Deep purple | trousers and cap", (0.23, 0.12, 0.55))
pink = mat("Parcel Panic pink | jacket", (0.92, 0.20, 0.48))
cyan = mat("Bright cyan | delivery backpack", (0.03, 0.68, 0.82))
lime = mat("Lime details", (0.58, 0.83, 0.13))
skin = mat("Warm skin", (0.72, 0.43, 0.27))
dark = mat("Dark navy | shoes and details", (0.08, 0.10, 0.20))
white = mat("Warm white", (0.94, 0.92, 0.84))
cardboard = mat("Parcel cardboard", (0.65, 0.40, 0.20))
tape = mat("Parcel tape", (0.96, 0.74, 0.31))

def finish(obj, name, material, bevel=0):
    obj.name = name
    if material: obj.data.materials.append(material)
    if bevel:
        mod = obj.modifiers.new("Soft low-poly edges", 'BEVEL')
        mod.width, mod.segments = bevel, 1
        obj.modifiers.new("Weighted corner normals", 'WEIGHTED_NORMAL')
    return obj

def cube(name, loc, scale, material, bevel=0.06, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o=bpy.context.object; o.dimensions=scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rot: o.rotation_euler=rot
    return finish(o,name,material,bevel)

def ico(name, loc, scale, material, subdivisions=2):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=subdivisions, radius=1, location=loc)
    o=bpy.context.object; o.scale=scale
    return finish(o,name,material)

def uvball(name, loc, scale, material, segments=32, rings=20):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings, radius=1, location=loc)
    o=bpy.context.object; o.scale=scale
    for p in o.data.polygons: p.use_smooth=True
    return finish(o,name,material)

def seam(name, points, material, bevel=0.012):
    curve=bpy.data.curves.new(name,"CURVE"); curve.dimensions='3D'; curve.bevel_depth=bevel; curve.bevel_resolution=3
    spl=curve.splines.new('POLY'); spl.points.add(len(points)-1)
    for p,co in zip(spl.points,points): p.co=(*co,1)
    obj=bpy.data.objects.new(name,curve); bpy.context.collection.objects.link(obj); obj.data.materials.append(material)
    return obj

def link(name, a, b, radius, material, vertices=8):
    a,b=Vector(a),Vector(b); d=b-a
    bpy.ops.mesh.primitive_cylinder_add(vertices=vertices, radius=radius, depth=d.length, location=(a+b)/2)
    o=bpy.context.object; o.rotation_mode='QUATERNION'; o.rotation_quaternion=d.to_track_quat('Z','Y')
    return finish(o,name,material)

# Ground origin is between the feet; the character faces +Y and Z is up.
# Running pose, with the backpack clearly visible from the rear three-quarter view.
cube("Jacket | short-sleeved body", (0,0,1.55), (0.76,0.46,0.76), pink, .11, (math.radians(-5),0,0))
cube("Jacket hem", (0,0.015,1.19), (.72,.45,.13), purple, .035)

# Legs in a stride. Each is its own simple piece, ready to replace or rig in Unity.
link("Left thigh", (-.20,0,1.17), (-.29,.16,.70), .145, purple)
ico("Left knee",(-.29,.16,.70),(.15,.15,.15),purple)
link("Left shin", (-.29,.16,.68), (-.34,.39,.25), .105, purple)
ico("Left ankle",(-.34,.39,.24),(.11,.11,.10),dark)
cube("Left trainer", (-.34,.48,.12), (.25,.40,.20), dark, .07, (math.radians(-8),0,math.radians(-6)))
cube("Left trainer sole", (-.34,.49,.045), (.27,.42,.065), white, .025, (math.radians(-8),0,math.radians(-6)))

link("Right thigh", (.20,0,1.17), (.28,-.02,.73), .145, purple)
ico("Right knee",(.28,-.02,.73),(.15,.15,.15),purple)
link("Right shin", (.28,-.02,.71), (.38,-.31,.29), .105, purple)
ico("Right ankle",(.38,-.31,.28),(.11,.11,.10),dark)
cube("Right trainer", (.38,-.40,.13), (.25,.40,.20), dark, .07, (math.radians(8),0,math.radians(5)))
cube("Right trainer sole", (.38,-.41,.045), (.27,.42,.065), white, .025, (math.radians(8),0,math.radians(5)))

# Head and backward-facing cap (brim points toward -Y).
uvball("Head",(0,.025,2.16),(.30,.28,.34),skin)
uvball("Hair",(0,-.015,2.33),(.31,.29,.20),dark,24,16)
uvball("Cap crown",(0,-.045,2.43),(.34,.32,.20),purple)
cube("Cap brim | backwards", (0,-.36,2.39), (.40,.34,.055), purple,.025)
cube("Cap band", (0,-.11,2.32), (.47,.035,.06), lime,.015)

# Backpack: bright, readable rectangle, carried high on the back (-Y).
cube("Backpack | main body", (0,-.31,1.58), (.69,.32,.73), cyan,.10)
cube("Backpack | front pocket", (0,-.493,1.45), (.47,.08,.27), cyan,.045)
cube("Backpack | flap", (0,-.505,1.83), (.57,.075,.13), lime,.025)
for x in (-.25,.25):
    cube("Backpack strap", (x,-.105,1.60), (.075,.075,.55), purple,.025)
cube("Parcel Panic bag badge", (0,-.545,1.60), (.18,.025,.15), white,.018)
cube("Backpack side pocket L",(-.365,-.28,1.47),(.10,.22,.31),purple,.035)
cube("Backpack side pocket R",(.365,-.28,1.47),(.10,.22,.31),purple,.035)
for x in (-.25,.25):
    cube("Backpack strap buckle",(x,-.12,1.55),(.105,.035,.075),lime,.012)
seam("Backpack pocket piping",[(-.23,-.541,1.58),(-.23,-.541,1.34),(0,-.541,1.31),(.23,-.541,1.34),(.23,-.541,1.58)],purple,.012)

# Opposite arm swing, with a small parcel tucked in the courier's hand.
link("Left upper arm", (-.39,-.01,1.79), (-.55,-.11,1.48), .115, pink)
ico("Left elbow",(-.55,-.11,1.48),(.12,.12,.12),skin)
link("Left forearm", (-.55,-.11,1.48), (-.48,-.30,1.27), .085, pink)
ico("Left hand",(-.48,-.30,1.24),(.105,.09,.10),skin)

link("Right upper arm", (.39,-.01,1.79), (.55,.10,1.54), .115, pink)
ico("Right elbow",(.55,.10,1.54),(.12,.12,.12),skin)
link("Right forearm", (.55,.10,1.54), (.52,.34,1.42), .085, pink)
ico("Right hand",(.52,.34,1.40),(.105,.09,.10),skin)
cube("Parcel | held in right hand", (.58,.48,1.39), (.28,.28,.27), cardboard,.035, (0,0,math.radians(12)))
cube("Parcel tape", (.58,.48,1.39), (.055,.295,.28), tape,.008, (0,0,math.radians(12)))
cube("Parcel label", (.58,.63,1.41), (.11,.012,.07), white,.006, (0,0,math.radians(12)))

# Extra face and uniform details for this higher-detail reference version.
for x in (-.105,.105):
    uvball("Eye white",(x,.283,2.19),(.052,.025,.064),white,20,12)
    uvball("Eye pupil",(x,.306,2.19),(.022,.014,.032),dark,16,10)
seam("Friendly smile",[(-.075,.285,2.075),(-.04,.299,2.055),(0,.302,2.05),(.04,.299,2.055),(.075,.285,2.075)],dark,.009)
cube("Cap front badge",(0,.247,2.42),(.16,.026,.10),lime,.018)
cube("Jacket front zip",(0,.239,1.58),(.026,.018,.47),purple,.008)
cube("Jacket zip pull",(0,.254,1.39),(.065,.018,.035),lime,.008)
for x in (-.22,.22):
    cube("Jacket chest pocket",(x,.244,1.68),(.18,.028,.16),pink,.025)
    seam("Pocket stitch",[(x-.065,.261,1.70),(x+.065,.261,1.70),(x+.065,.261,1.60),(x-.065,.261,1.60),(x-.065,.261,1.70)],white,.005)
    cube("Sleeve cuff",(x*1.85,0,1.55),(.22,.34,.09),lime,.025)
cube("Jacket collar L",(-.17,.19,1.91),(.22,.13,.09),purple,.025,(0,0,math.radians(-18)))
cube("Jacket collar R",(.17,.19,1.91),(.22,.13,.09),purple,.025,(0,0,math.radians(18)))
for x in (-.06,.06):
    uvball("Trainer lace",(x,.635,.15),(.035,.014,.014),white,16,8)

# A ground shadow, camera and soft studio lighting make the saved file easy to preview.
floor_mat=mat("Studio floor",(.91,.89,.96))
cube("Display ground", (0,0,-.09),(200,200,.1),floor_mat,.0)
world=bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world=world; world.color=(.78,.78,.78)
bpy.ops.object.light_add(type='AREA', location=(4,-5,7)); key=bpy.context.object; key.name="Large softbox"; key.data.energy=900; key.data.shape='DISK'; key.data.size=5
bpy.ops.object.light_add(type='AREA', location=(-4,3,5)); fill=bpy.context.object; fill.name="Back fill"; fill.data.energy=700; fill.data.size=4
bpy.ops.object.camera_add(location=(4.0,-6.5,3.3)); cam=bpy.context.object; cam.name="Courier preview camera"
cam.rotation_euler=(Vector((0,0,1.19))-cam.location).to_track_quat('-Z','Y').to_euler(); cam.data.type='ORTHO'; cam.data.ortho_scale=3.65
scene=bpy.context.scene; scene.camera=cam
scene.render.engine='BLENDER_EEVEE_NEXT'
scene.render.resolution_x=1200; scene.render.resolution_y=1200; scene.render.resolution_percentage=100
scene.render.image_settings.file_format='PNG'; scene.render.film_transparent=False
scene.view_settings.view_transform='Standard'; scene.view_settings.look='Medium High Contrast'; scene.view_settings.exposure=0; scene.view_settings.gamma=1
scene.render.filepath=os.path.join(OUT,"parcel-panic-courier-reference.png")
scene.camera.data.lens=50

# Keep the ground out of the export; Unity can supply its own ground and lighting.
ground=bpy.data.objects.get("Display ground")
ground.hide_render=False
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(OUT,"ParcelPanicCourier_Reference.blend"))
bpy.ops.render.render(write_still=True)
ground.hide_set(True)
bpy.ops.object.select_all(action='DESELECT')
for o in bpy.context.scene.objects:
    if o.name not in {"Display ground", "Large softbox", "Back fill", "Courier preview camera"}:
        o.select_set(True)
bpy.context.view_layer.objects.active=bpy.data.objects.get("Jacket | short-sleeved body")
bpy.ops.export_scene.gltf(filepath=os.path.join(OUT,"ParcelPanicCourier.glb"), export_format='GLB', use_selection=True, export_apply=True)
print("Wrote Blender source, GLB export and preview to", OUT)
