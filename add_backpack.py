"""Add the courier's delivery backpack to the rigged + animated character.

Run:  Blender -b Art/MainCharacter/main_character_v011_walk.blend --python add_backpack.py -- <out.blend>

What it makes (collection "Backpack"):
  Bag         the box: body, lid, dark rounded edges, top handle and the parcel-cube logo.
              It is hard, so it follows the chest bone 100% (like the cap follows the head).
  Bag_Straps  two padded shoulder straps, adjuster buckles and a chest strap.
              They lie on the jacket and copy the jacket's weights, so they bend with the
              shoulders; the ends near the bag blend to the chest bone so they stay attached.

Change the numbers in the STYLE block and run again (it replaces an old bag if there is one).
"""
import bpy
import bmesh
import math
import sys
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

OUT = sys.argv[sys.argv.index("--") + 1]

# ---------------------------------------------------------------------------
# STYLE - all sizes in metres (the character is 1.72 m tall)
# ---------------------------------------------------------------------------
BAG_WIDTH = 0.30        # left-right. Wider than ~0.32 and the swinging arms hit it
BAG_HEIGHT = 0.38       # top to bottom
BAG_DEPTH = 0.22        # how far it sticks out behind the back
BAG_TOP = 1.30          # height of the top of the bag (shoulders are at ~1.33)
BAG_GAP = 0.016         # space between the jacket and the bag
EDGE = 0.022            # size of the dark rounded edges
LID = 0.075             # height of the lid
LOGO_SIZE = 0.155       # height of the parcel-cube logo on the back
STRAP_WIDTH = 0.046     # padded shoulder strap
STRAP_THICK = 0.011
WEB_WIDTH = 0.030       # thin webbing from the buckle back to the bottom of the bag
WEB_THICK = 0.004
COLOURS = {             # same style of colour values as the other character materials
    "BagYellow":    (0.98, 0.66, 0.10),
    "BagTrim":      (0.07, 0.07, 0.09),
    "BagStrap":     (0.10, 0.10, 0.12),
    "BagBuckle":    (0.55, 0.56, 0.62),
    "BagLogoTop":   (1.00, 1.00, 1.00),
    "BagLogoLeft":  (0.86, 0.86, 0.91),
    "BagLogoRight": (0.70, 0.71, 0.79),
}

rig = bpy.data.objects["CourierRig"]
jacket = bpy.data.objects["Jacket"]

# ---------------------------------------------------------------------------
# Start clean: remove an old bag, build everything in the rest pose
# ---------------------------------------------------------------------------
for o in [o for o in bpy.data.objects if o.name.startswith(("Bag", "TorsoOnly"))]:
    bpy.data.objects.remove(o, do_unlink=True)
for me in [me for me in bpy.data.meshes if me.users == 0]:
    bpy.data.meshes.remove(me)
rig.data.pose_position = 'REST'
dg = bpy.context.evaluated_depsgraph_get()
dg.update()


def material(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    rgba = (*COLOURS[name], 1.0)
    m.diffuse_color = rgba                    # colour in the viewport / Workbench
    m.use_nodes = True
    bsdf = m.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = rgba   # colour that goes to the FBX / Unity
    bsdf.inputs["Roughness"].default_value = 0.6 if name != "BagBuckle" else 0.4
    return m


ARM_BONES = ("upper_arm", "forearm", "hand")


def seg_dist(p, a, b):
    ab = b - a
    t = max(0.0, min(1.0, (p - a).dot(ab) / ab.length_squared))
    return (p - (a + ab * t)).length


SEGS = [(bn.name.startswith(ARM_BONES), rig.matrix_world @ bn.head_local, rig.matrix_world @ bn.tail_local)
        for bn in rig.data.bones
        if bn.name.split(".")[0] in ("hips", "spine", "chest", "neck", "shoulder", "upper_arm", "forearm", "hand")]


def is_sleeve(p):
    """Sleeve if the point is much closer to an arm bone than to the spine/shoulder bones."""
    d_arm = min(seg_dist(p, a, b) for arm, a, b in SEGS if arm)
    d_body = min(seg_dist(p, a, b) for arm, a, b in SEGS if not arm)
    return d_arm * 2.5 < d_body


def torso_surface():
    """BVH of the outside of the jacket + t-shirt in the rest pose, without the sleeves."""
    bm = bmesh.new()
    for name in ("Jacket", "Jacket_Collar", "Jacket_Bands", "Jacket_Details", "TShirt"):
        ob = bpy.data.objects[name]
        ev = ob.evaluated_get(dg)
        me = ev.to_mesh()
        me.transform(ob.matrix_world)
        tmp = bmesh.new()
        tmp.from_mesh(me)
        bmesh.ops.delete(tmp, geom=[f for f in tmp.faces if is_sleeve(f.calc_center_median())],
                         context='FACES')
        mesh_tmp = bpy.data.meshes.new("tmp")
        tmp.to_mesh(mesh_tmp)
        tmp.free()
        bm.from_mesh(mesh_tmp)
        bpy.data.meshes.remove(mesh_tmp)
        ev.to_mesh_clear()
    tree = BVHTree.FromBMesh(bm)
    bm.free()
    return tree


SURF = torso_surface()

# ---------------------------------------------------------------------------
# Where the bag goes: just behind the jacket, centred on the spine
# ---------------------------------------------------------------------------
W, H, D = BAG_WIDTH, BAG_HEIGHT, BAG_DEPTH
zt, zb = BAG_TOP, BAG_TOP - BAG_HEIGHT
back = 0.0
for i in range(13):
    for k in range(13):
        x = -W / 2 + W * i / 12
        z = zb + H * k / 12
        hit = SURF.ray_cast(Vector((x, 0.6, z)), Vector((0, -1, 0)))[0]
        if hit:
            back = max(back, hit.y)
y0 = back + BAG_GAP                 # face of the bag that touches the back
yc = y0 + D / 2
print(f"BAG  back of jacket y={back:.3f}  bag y={y0:.3f}..{y0 + D:.3f}  z={zb:.3f}..{zt:.3f}  width={W}")


def oriented_box(bm, c, axes, half, mat, bevel=0.0, segs=4, bevel_mat=None):
    """Box at c with axes (ax, ay, az) and half sizes; optional rounded (bevelled) edges."""
    ret = bmesh.ops.create_cube(bm, size=2.0)
    vs = ret['verts']
    ax, ay, az = axes
    for v in vs:
        x, y, z = v.co
        v.co = c + ax * (x * half[0]) + ay * (y * half[1]) + az * (z * half[2])
    for f in {f for v in vs for f in v.link_faces}:
        f.material_index = mat
    if bevel > 0:
        edges = list({e for v in vs for e in v.link_edges})
        r = bmesh.ops.bevel(bm, geom=edges, offset=bevel, segments=segs, profile=0.5,
                            affect='EDGES', clamp_overlap=True)
        for f in r['faces']:
            f.material_index = mat if bevel_mat is None else bevel_mat


X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))

# ---------------------------------------------------------------------------
# The bag: body + lid + logo + handle   (materials 0 yellow, 1 trim, 2-4 logo)
# ---------------------------------------------------------------------------
bm = bmesh.new()
body_top = zt - LID + 0.01
oriented_box(bm, Vector((0, yc, (zb + body_top) / 2)), (X, Y, Z),
             (W / 2, D / 2, (body_top - zb) / 2), 0, EDGE, 4, 1)
oriented_box(bm, Vector((0, yc, zt - LID / 2)), (X, Y, Z),
             (W / 2 + 0.006, D / 2 + 0.006, LID / 2), 0, EDGE * 0.8, 4, 1)

# parcel-cube logo on the back: three diamonds (top, left, right) with thin gaps between them
yl = y0 + D + 0.0005
zl = (zb + EDGE + zt - LID) / 2
R = LOGO_SIZE / 2


def hexpt(deg):
    # seen from behind the character, "right" is -X
    a = math.radians(deg)
    return Vector((-R * math.cos(a), yl, zl + R * math.sin(a)))


C = Vector((0, yl, zl))
for corners, mat in (((C, hexpt(150), hexpt(90), hexpt(30)), 2),     # top
                     ((C, hexpt(270), hexpt(210), hexpt(150)), 3),   # left
                     ((C, hexpt(30), hexpt(330), hexpt(270)), 4)):   # right
    cen = sum(corners, Vector()) / 4
    vs = [bm.verts.new(cen + (p - cen) * 0.86) for p in corners]
    f = bm.faces.new(vs)
    f.material_index = mat
    f.normal_update()
    if f.normal.y < 0:
        f.normal_flip()
    ext = bmesh.ops.extrude_face_region(bm, geom=[f])
    new_vs = [g for g in ext['geom'] if isinstance(g, bmesh.types.BMVert)]
    bmesh.ops.translate(bm, verts=new_vs, vec=Vector((0, 0.003, 0)))
    for g in ext['geom']:
        if isinstance(g, bmesh.types.BMFace):
            g.material_index = mat
    bmesh.ops.delete(bm, geom=[f], context='FACES')


def tube(bm, pts, radius, mat, segs=10):
    rings = []
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = t.cross(Y).normalized()
        b = t.cross(n).normalized()
        rings.append([bm.verts.new(p + radius * (math.cos(2 * math.pi * k / segs) * n +
                                                 math.sin(2 * math.pi * k / segs) * b))
                      for k in range(segs)])
    for a, b in zip(rings, rings[1:]):
        for k in range(segs):
            bm.faces.new((a[k], a[(k + 1) % segs], b[(k + 1) % segs], b[k])).material_index = mat
    for ring in (rings[0], rings[-1]):
        bm.faces.new(ring).material_index = mat


# carry handle on the lid
tube(bm, [Vector((-0.065 * math.cos(math.pi * s / 16), yc,
                  zt - 0.010 + 0.030 * math.sin(math.pi * s / 16) ** 0.6)) for s in range(17)], 0.009, 1)

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    f.smooth = True
for e in bm.edges:   # crisp edge where the colour changes, and on the flat logo
    mats = {f.material_index for f in e.link_faces}
    if len(mats) > 1 or (mats and min(mats) >= 2) or e.calc_face_angle(0) > math.radians(40):
        e.smooth = False
bag_me = bpy.data.meshes.new("Bag")
bm.to_mesh(bag_me)
bm.free()
bag = bpy.data.objects.new("Bag", bag_me)
for name in ("BagYellow", "BagTrim", "BagLogoTop", "BagLogoLeft", "BagLogoRight"):
    bag_me.materials.append(material(name))

# ---------------------------------------------------------------------------
# Shoulder straps: a path from the top of the bag, over the shoulder, down the chest,
# round the side and back into the bottom of the bag. Each point is pushed onto the
# jacket (along a "this way is outside" hint) so the strap lies on it.
# ---------------------------------------------------------------------------
def strap_path(s):
    """Control points (position, outside-hint, inside-the-bag?) for side s=+1 (left) / -1."""
    P = [((0.090, y0 + 0.040, zt - 0.040), (0, 1, 0), True),
         ((0.100, y0 - 0.006, zt + 0.004), (0, 1, 1), True),
         ((0.122, 0.088, 1.336), (0, 0.6, 1), False),
         ((0.134, 0.040, 1.352), (0.25, 0, 1), False),
         ((0.134, -0.012, 1.348), (0.25, -0.3, 1), False),
         ((0.130, -0.062, 1.318), (0.1, -0.8, 0.7), False),
         ((0.123, -0.100, 1.262), (0, -1, 0.3), False),
         ((0.119, -0.114, 1.185), (0, -1, 0), False),
         ((0.120, -0.118, 1.125), (0, -1, 0), False),
         ((0.134, -0.108, 1.078), (0.3, -1, 0), False),    # adjuster buckle: webbing from here on
         # under the arm the webbing stays low and towards the back: the swinging arms
         # brush the jacket higher up
         ((0.168, -0.055, 1.020), (1, -0.7, 0), False),
         ((0.184, 0.010, 0.982), (1, 0, 0), False),
         ((0.166, 0.075, 0.968), (0.7, 0.7, 0), False),
         ((0.128, y0 - 0.006, zb + 0.050), (0, 1, 0), True),
         ((0.112, y0 + 0.040, zb + 0.060), (0, 1, 0), True)]
    return [(Vector((s * x, y, z)), Vector((s * hx, hy, hz)).normalized(), inside)
            for (x, y, z), (hx, hy, hz), inside in P]


def catmull(ctrl, step=0.011):
    pts, hints, fixed = [], [], []
    n = len(ctrl)
    for i in range(n - 1):
        p0, p1, p2, p3 = (ctrl[max(i - 1, 0)][0], ctrl[i][0], ctrl[i + 1][0], ctrl[min(i + 2, n - 1)][0])
        k = max(2, math.ceil((p2 - p1).length / step))
        for j in range(k):
            t = j / k
            p = 0.5 * ((2 * p1) + (-p0 + p2) * t + (2 * p0 - 5 * p1 + 4 * p2 - p3) * t * t +
                       (-p0 + 3 * p1 - 3 * p2 + p3) * t * t * t)
            pts.append(p)
            hints.append((ctrl[i][1] * (1 - t) + ctrl[i + 1][1] * t).normalized())
            fixed.append(ctrl[i][2] and (t < 0.5 or ctrl[i + 1][2]))
    pts.append(ctrl[-1][0].copy())
    hints.append(ctrl[-1][1])
    fixed.append(True)
    return pts, hints, fixed


GAP = 0.004   # space between jacket and strap


def settle(p, hint):
    """Push p out of the jacket so it sits GAP above it; return (point, surface normal)."""
    hit, nrm, _, _ = SURF.ray_cast(p + hint * 0.06, -hint, 0.14)
    if hit is None:
        return p, hint
    if nrm.dot(hint) < 0:
        nrm = -nrm
    if (p - hit).dot(nrm) < GAP:
        p = hit + nrm * GAP
    return p, nrm


def build_strap_line(s):
    pts, hints, fixed = catmull(strap_path(s))
    nrms = list(hints)
    for it in range(5):
        for i in range(len(pts)):
            if not fixed[i]:
                pts[i], nrms[i] = settle(pts[i], hints[i])
        if it == 4:
            break
        new = [p.copy() for p in pts]
        for i in range(1, len(pts) - 1):
            if not fixed[i]:
                new[i] = pts[i] * 0.5 + (pts[i - 1] + pts[i + 1]) * 0.25
        pts = new
    # smooth "up" direction along the strap so it does not twist
    ups = [(n + h).normalized() for n, h in zip(nrms, hints)]
    for _ in range(6):
        ups = [ups[0]] + [(ups[i - 1] + 2 * ups[i] + ups[i + 1]).normalized()
                          for i in range(1, len(ups) - 1)] + [ups[-1]]
    return pts, ups


def frames(pts, ups):
    out, prev_b = [], None
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        n = (ups[i] - t * ups[i].dot(t)).normalized()
        b = t.cross(n).normalized()
        if prev_b is not None and b.dot(prev_b) < 0:
            b = -b
        prev_b = b
        out.append((t, n, b))
    return out


def profile(hw, ht, k=12):
    for i in range(k):
        a = 2 * math.pi * (i + 0.5) / k
        c, s = math.cos(a), math.sin(a)
        yield hw * math.copysign(abs(c) ** 0.35, c), ht * math.copysign(abs(s) ** 0.35, s)


def sweep(bm, pts, frs, hw, ht, mat):
    prof = list(profile(hw, ht))
    rings = []
    for p, (t, n, b) in zip(pts, frs):
        c = p + n * ht
        rings.append([bm.verts.new(c + b * u + n * v) for u, v in prof])
    m = len(prof)
    for a, c in zip(rings, rings[1:]):
        for k in range(m):
            bm.faces.new((a[k], a[(k + 1) % m], c[(k + 1) % m], c[k])).material_index = mat
    for ring in (rings[0], rings[-1]):
        bm.faces.new(ring).material_index = mat


bm = bmesh.new()
chest_x = {}
for s in (1, -1):
    pts, ups = build_strap_line(s)
    frs = frames(pts, ups)
    # padded strap down to the adjuster buckle, thin webbing after it
    i = min(range(len(pts)), key=lambda j: (pts[j] - Vector((s * 0.134, -0.108, 1.078))).length)
    sweep(bm, pts[:i + 2], frs[:i + 2], STRAP_WIDTH / 2, STRAP_THICK / 2, 0)
    sweep(bm, pts[i - 1:], frs[i - 1:], WEB_WIDTH / 2, WEB_THICK / 2, 0)
    t, n, b = frs[i]
    oriented_box(bm, pts[i] + n * (STRAP_THICK / 2), (t, b, n),
                 (0.011, STRAP_WIDTH / 2 + 0.006, STRAP_THICK / 2 + 0.003), 1, 0.002, 2)
    front = [j for j in range(len(pts)) if pts[j].y < -0.08]
    chest_x[s] = pts[min(front, key=lambda j: abs(pts[j].z - 1.175))].x

# chest strap: straight across the open jacket, in front of the zip, with a buckle in the middle
CZ = 1.175
front_y = min((h.y for h in (SURF.ray_cast(Vector((x / 400, -0.6, CZ + dz)), Vector((0, 1, 0)))[0]
                             for x in range(-56, 57) for dz in (-0.014, -0.007, 0, 0.007, 0.014))
                if h is not None), default=-0.12)
cy = min(front_y - GAP, -0.118 - STRAP_THICK) - 0.003     # rests on the shoulder straps
L, Rt = Vector((chest_x[1], cy, CZ)), Vector((chest_x[-1], cy, CZ))
t, n = (Rt - L).normalized(), Vector((0, -1, 0))
b = t.cross(n).normalized()
seg = [L.lerp(Rt, k / 10) for k in range(11)]
sweep(bm, [p - n * 0.003 for p in seg], [(t, n, b)] * len(seg), 0.011, 0.003, 0)
oriented_box(bm, (L + Rt) / 2 + n * 0.004, (t, b, n), (0.019, 0.014, 0.006), 1, 0.003, 2)
print(f"CHEST STRAP  front of jacket/zip y={front_y:.3f}  strap y={cy:.3f}")

bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
for f in bm.faces:
    f.smooth = True
straps_me = bpy.data.meshes.new("Bag_Straps")
bm.to_mesh(straps_me)
bm.free()
straps = bpy.data.objects.new("Bag_Straps", straps_me)
for name in ("BagStrap", "BagBuckle"):
    straps_me.materials.append(material(name))

# ---------------------------------------------------------------------------
# Put them in the scene and skin them
# ---------------------------------------------------------------------------
coll = bpy.data.collections.get("Backpack") or bpy.data.collections.new("Backpack")
if coll.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(coll)
for ob in (bag, straps):
    coll.objects.link(ob)


def ctx(obj):
    return bpy.context.temp_override(object=obj, active_object=obj,
                                     selected_objects=[obj], selected_editable_objects=[obj])


def add_armature_mod(ob):
    mod = ob.modifiers.new("Armature", 'ARMATURE')
    mod.object = rig
    with ctx(ob):
        bpy.ops.object.modifier_move_to_index(modifier=mod.name, index=0)
    ob.parent = rig
    ob.matrix_parent_inverse = rig.matrix_world.inverted()


def clean_weights(ob, limit=4, eps=0.01):
    """Max 4 bones per vertex (Unity default) and weights that add up to 1."""
    vgs = ob.vertex_groups
    empty = 0
    for vert in ob.data.vertices:
        ws = sorted(((g.group, g.weight) for g in vert.groups if g.weight > eps),
                    key=lambda x: -x[1])[:limit]
        for g in list(vert.groups):
            vgs[g.group].remove([vert.index])
        tot = sum(w for _, w in ws)
        if tot <= 0:
            empty += 1
            continue
        for gi, w in ws:
            vgs[gi].add([vert.index], w / tot, 'REPLACE')
    return empty


# the bag box: 100% chest bone
vg = bag.vertex_groups.new(name="chest")
vg.add([v.index for v in bag_me.vertices], 1.0, 'REPLACE')
add_armature_mod(bag)

# the straps: copy weights from the jacket's body (not its sleeves)
torso = bpy.data.objects.new("TorsoOnly", jacket.data.copy())
coll.objects.link(torso)
arm_groups = {g.index for g in torso.vertex_groups if g.name.startswith(ARM_BONES)}
bm = bmesh.new()
bm.from_mesh(torso.data)
deform = bm.verts.layers.deform.active
sleeve = [sum(w for gi, w in v[deform].items() if gi in arm_groups) > 0.5 for v in bm.verts]
bmesh.ops.delete(bm, geom=[f for f in bm.faces if sum(sleeve[v.index] for v in f.verts) * 2 > len(f.verts)],
                 context='FACES')
bm.to_mesh(torso.data)
bm.free()
for bone in rig.data.bones:
    if bone.use_deform:
        straps.vertex_groups.new(name=bone.name)
dt = straps.modifiers.new("WeightCopy", 'DATA_TRANSFER')
dt.object = torso
dt.use_object_transform = True
dt.use_vert_data = True
dt.data_types_verts = {'VGROUP_WEIGHTS'}
dt.vert_mapping = 'POLYINTERP_NEAREST'
dt.layers_vgroup_select_src = 'ALL'
dt.layers_vgroup_select_dst = 'NAME'
with ctx(straps):
    bpy.ops.object.modifier_apply(modifier=dt.name)
bpy.data.objects.remove(torso, do_unlink=True)

# straps are upper-body only: weight the jacket gave to the thighs goes to the hips
hips_vg = straps.vertex_groups["hips"]
for leg in [g for g in straps.vertex_groups if g.name.startswith(("thigh", "shin", "foot", "toe"))]:
    for v in straps_me.vertices:
        for g in v.groups:
            if g.group == leg.index and g.weight > 0:
                hips_vg.add([v.index], g.weight, 'ADD')
    straps.vertex_groups.remove(leg)

# near and inside the bag the straps follow the chest, so they stay fixed to the bag
chest_vg = straps.vertex_groups["chest"]
for v in straps_me.vertices:
    f = min(1.0, max(0.0, (v.co.y - 0.070) / (y0 - 0.070)))
    f = f * f * (3 - 2 * f)
    if f <= 0:
        continue
    for g in v.groups:
        g.weight *= (1 - f)
    chest_vg.add([v.index], f, 'ADD')
print("STRAPS unweighted verts:", clean_weights(straps))
used = {g.group for v in straps_me.vertices for g in v.groups}
for g in [g for g in straps.vertex_groups if g.index not in used]:
    straps.vertex_groups.remove(g)
print("STRAPS bones:", sorted(g.name for g in straps.vertex_groups))
add_armature_mod(straps)
straps.modifiers.new("Subdivision", 'SUBSURF').levels = 1
straps.modifiers["Subdivision"].render_levels = 1

print(f"BAG verts={len(bag_me.vertices)}  STRAPS verts={len(straps_me.vertices)}")
rig.data.pose_position = 'POSE'
bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED", OUT)
