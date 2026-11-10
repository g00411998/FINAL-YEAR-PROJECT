"""Rig main_character_v009 -> main_character_v010_rig (Steps 1-4, with proper hands).

Run:  Blender -b main_character_v009.blend --python rig_character.py -- <out.blend>
"""
import bpy
import sys
from mathutils import Vector, Matrix

OUT = sys.argv[sys.argv.index("--") + 1]

# ---------------------------------------------------------------------------
# Which meshes belong to the character
# ---------------------------------------------------------------------------
CHAR_COLLS = ("Character", "Clothes")
char_meshes = [o for o in bpy.data.objects
               if o.type == 'MESH' and any(c.name in CHAR_COLLS for c in o.users_collection)]

# Rigid parts that should follow the head bone 100%
HEAD_RIGID = {"Head", "Ears", "Eye.L", "Eye.R", "Eyebrows", "Eyelashes",
              "Hair_Base", "Hair_Clumps", "Cap", "Cap_Brim", "Cap_Strap"}
# Clothes that copy their weights from the body
CLOTHES = [o for o in char_meshes if o.name not in HEAD_RIGID and o.name != "Body"]
body = bpy.data.objects["Body"]

# Read joint positions from the Skin-modifier skeleton of the body BEFORE we apply it
J = {i: v.co.copy() for i, v in enumerate(body.data.vertices)}


def ctx(obj, selected=None):
    sel = selected if selected is not None else [obj]
    return bpy.context.temp_override(object=obj, active_object=obj,
                                     selected_objects=sel, selected_editable_objects=sel)


# ---------------------------------------------------------------------------
# STEP 1 - Prepare the model
# ---------------------------------------------------------------------------
print("STEP 1: prepare")
for ob in char_meshes:
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    # apply every modifier except Subdivision (kept live so you can lower it for the game)
    for m in [m for m in ob.modifiers if m.type != 'SUBSURF']:
        with ctx(ob):
            bpy.ops.object.modifier_apply(modifier=m.name)
    # apply transforms (no parents, so matrix_basis == world)
    if ob.matrix_basis != Matrix.Identity(4):
        ob.data.transform(ob.matrix_basis)
        ob.matrix_basis = Matrix.Identity(4)
    print(f"  {ob.name:18s} verts={len(ob.data.vertices):6d} mods={[m.type for m in ob.modifiers]}")

# ---------------------------------------------------------------------------
# STEP 1b - Proper hands: cut the paddle hand off the body, build hands with fingers
# ---------------------------------------------------------------------------
import bmesh

HS = 1.1                                   # overall hand size
COL_U = [-0.042, -0.021, 0.0, 0.021, 0.042]          # knuckle columns, index side -> pinky side
KNUCKLE_W = [0.080, 0.086, 0.086, 0.082, 0.073]      # how far each knuckle column is from the wrist
PALM_RINGS = [  # (distance from wrist, width scale, half thickness)  None = knuckle line
    (-0.05, 0.60, 0.016),                  # inside the sleeve
    (0.0, 0.66, 0.0175),                   # wrist
    (0.045, 0.94, 0.0165),                 # middle of the palm
    (None, 1.0, 0.0140),                   # knuckles
]
FINGERS = [  # name, length, half width, half thickness, spread (toward pinky side)
    ("index", 0.074, 0.0097, 0.0090, -0.07),
    ("middle", 0.082, 0.0101, 0.0093, 0.0),
    ("ring", 0.077, 0.0096, 0.0089, 0.06),
    ("pinky", 0.060, 0.0083, 0.0078, 0.14),
]
SEGS = (0.45, 0.30, 0.25)                  # finger bone lengths as part of the finger
THUMB = (0.068, (0.40, 0.33, 0.27))        # length, segments


def hand_frame(sx):
    """Wrist position and the hand's axes: U across (index->pinky), V back of hand, W along."""
    m = lambda q: Vector((q.x * sx, q.y, q.z))
    wrist, tip = m(J[14]), m(J[16])
    W = (tip - wrist).normalized()
    v0 = Vector((sx, -0.35, 0.0))          # back of hand faces out (and a bit forward): palm faces the leg
    V = (v0 - v0.dot(W) * W).normalized()
    U = W.cross(V).normalized()
    if U.y < 0:                            # index finger at the front, pinky at the back
        U = -U
    return wrist, U, V, W


def build_hand(side, verts, faces, wts, bones):
    sx = 1 if side == "L" else -1
    O, U, V, W = hand_frame(sx)
    P = lambda a, b, c: O + HS * (a * U + b * V + c * W)
    F = lambda n: f"{n}.{side}"

    def add(p, weights):
        verts.append(p)
        wts.append(weights)
        return len(verts) - 1

    # palm: 4 rings of 10 verts (back c0..c4, palm c4..c0)
    ring_w = [{F("forearm"): 1.0}, {F("forearm"): 0.5, F("hand"): 0.5}, {F("hand"): 1.0}, {F("hand"): 1.0}]
    rings = []
    for ri, (wpos, ws, ht) in enumerate(PALM_RINGS):
        ring = []
        for back in (True, False):
            for c in (range(5) if back else range(4, -1, -1)):
                ww = KNUCKLE_W[c] if wpos is None else wpos
                vv = ht * (0.72 if c in (0, 4) else 1.0) * (1 if back else -1)
                if ri == 2 and not back and c in (0, 1):
                    vv -= 0.005                                  # fleshy thumb pad
                ring.append(add(P(COL_U[c] * ws, vv, ww), ring_w[ri]))
        rings.append(ring)
    back = lambda r, c: rings[r][c]
    palm = lambda r, c: rings[r][9 - c]
    for r in range(3):
        for k in range(10):
            a, b = rings[r][k], rings[r][(k + 1) % 10]
            if r == 1 and k == 9:
                continue                                         # hole where the thumb grows out
            faces.append((a, b, rings[r + 1][(k + 1) % 10], rings[r + 1][k]))

    def grow(port, center, d, e1, e2, profile):
        """Loft rings of 4 verts along d. profile: (distance, half width, half thickness, weights)."""
        prev = port
        for s, hw, ht, wt in profile:
            cen = center + d * (s * HS)
            ring = [add(cen + HS * (-hw * e1 + ht * e2), wt), add(cen + HS * (hw * e1 + ht * e2), wt),
                    add(cen + HS * (hw * e1 - ht * e2), wt), add(cen + HS * (-hw * e1 - ht * e2), wt)]
            for k in range(4):
                faces.append((prev[k], prev[(k + 1) % 4], ring[(k + 1) % 4], ring[k]))
            prev = ring
        faces.append(tuple(prev))                                # fingertip cap

    # fingers out of the knuckle line
    for i, (name, L, hw, ht, spread) in enumerate(FINGERS):
        port = [back(3, i), back(3, i + 1), palm(3, i + 1), palm(3, i)]
        center = sum((verts[p] for p in port), Vector()) / 4
        d = (W + spread * U).normalized()
        e1 = (U - U.dot(d) * d).normalized()
        b1, b2, b3 = (F(f"{name}.0{n}") for n in (1, 2, 3))
        l1, l2, l3 = (s * L for s in SEGS)
        grow(port, center, d, e1, V, [
            (0.006, hw * 0.95, ht * 1.05, {F("hand"): 0.6, b1: 0.4}),
            (l1 * 0.5, hw, ht, {b1: 1.0}),
            (l1, hw * 0.94, ht * 0.92, {b1: 0.5, b2: 0.5}),
            (l1 + l2 * 0.5, hw * 0.93, ht * 0.9, {b2: 1.0}),
            (l1 + l2, hw * 0.88, ht * 0.86, {b2: 0.5, b3: 0.5}),
            (l1 + l2 + l3 * 0.5, hw * 0.86, ht * 0.82, {b3: 1.0}),
            (L - 0.006, hw * 0.72, ht * 0.66, {b3: 1.0}),
            (L, hw * 0.34, ht * 0.30, {b3: 1.0}),
        ])
        tip = center + d * (L * HS)
        pts = [center, center + d * (l1 * HS), center + d * ((l1 + l2) * HS), tip]
        bones += [(b1, pts[0], pts[1], F("hand"), False), (b2, pts[1], pts[2], b1, True),
                  (b3, pts[2], pts[3], b2, True)]
        if name == "middle":
            bones.append(("HAND_TAIL", center, None, None, None))

    # thumb out of the side of the palm, angled toward the palm
    port = [back(1, 0), back(2, 0), palm(2, 0), palm(1, 0)]
    center = sum((verts[p] for p in port), Vector()) / 4
    d = (-0.55 * U - 0.42 * V + 0.72 * W).normalized()
    e1 = (W - W.dot(d) * d).normalized()
    e2 = d.cross(e1).normalized()
    if e2.dot(V) < 0:
        e2 = -e2
    L, segs = THUMB
    l1, l2, l3 = (s * L for s in segs)
    t1, t2, t3 = (F(f"thumb.0{n}") for n in (1, 2, 3))
    grow(port, center, d, e1, e2, [
        (0.010, 0.0150, 0.0125, {F("hand"): 0.55, t1: 0.45}),
        (l1 * 0.6, 0.0125, 0.0110, {t1: 1.0}),
        (l1, 0.0118, 0.0104, {t1: 0.5, t2: 0.5}),
        (l1 + l2 * 0.5, 0.0115, 0.0100, {t2: 1.0}),
        (l1 + l2, 0.0110, 0.0095, {t2: 0.5, t3: 0.5}),
        (l1 + l2 + l3 * 0.5, 0.0106, 0.0090, {t3: 1.0}),
        (L - 0.006, 0.0082, 0.0068, {t3: 1.0}),
        (L, 0.0040, 0.0034, {t3: 1.0}),
    ])
    base = center - d * (0.012 * HS)
    pts = [base, center + d * (l1 * HS), center + d * ((l1 + l2) * HS), center + d * (L * HS)]
    bones += [(t1, pts[0], pts[1], F("hand"), False), (t2, pts[1], pts[2], t1, True),
              (t3, pts[2], pts[3], t2, True)]
    return -V                                                    # palm direction (for bone roll)


# cut the old paddle hand off the body (keep the forearm up into the sleeve)
bm = bmesh.new()
bm.from_mesh(body.data)
for sx in (1, -1):
    O, U, V, W = hand_frame(sx)
    kill = [vt for vt in bm.verts if vt.co.x * sx > 0.2 and (vt.co - O).dot(W) > -0.03]
    bmesh.ops.delete(bm, geom=kill, context='VERTS')
bm.to_mesh(body.data)
bm.free()

hv, hf, hw_, HAND_BONES, PALM_DIR = [], [], [], {}, {}
for side in ("L", "R"):
    HAND_BONES[side] = []
    PALM_DIR[side] = build_hand(side, hv, hf, hw_, HAND_BONES[side])
hme = bpy.data.meshes.new("Hands")
hme.from_pydata([tuple(p) for p in hv], [], hf)
hme.update()
bm = bmesh.new()
bm.from_mesh(hme)
bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
bm.to_mesh(hme)
bm.free()
for poly in hme.polygons:
    poly.use_smooth = True
hme.materials.append(bpy.data.materials["Skin"])
hands = bpy.data.objects.new("Hands", hme)
bpy.data.collections["Character"].objects.link(hands)
hands.modifiers.new("Subdivision", 'SUBSURF').levels = 2
hands.modifiers["Subdivision"].render_levels = 2
for i, weights in enumerate(hw_):
    for g, wv in weights.items():
        vg = hands.vertex_groups.get(g) or hands.vertex_groups.new(name=g)
        vg.add([i], wv, 'REPLACE')
print(f"  Hands              verts={len(hme.vertices):6d} faces={len(hme.polygons)} (new, with fingers)")

# ---------------------------------------------------------------------------
# STEP 2 - Build the skeleton
# ---------------------------------------------------------------------------
print("STEP 2: skeleton")
rig_coll = bpy.data.collections.get("Rig") or bpy.data.collections.new("Rig")
if rig_coll.name not in bpy.context.scene.collection.children:
    bpy.context.scene.collection.children.link(rig_coll)

arm_data = bpy.data.armatures.new("CourierRig")
rig = bpy.data.objects.new("CourierRig", arm_data)
rig_coll.objects.link(rig)
rig.show_in_front = True
arm_data.display_type = 'OCTAHEDRAL'

v = lambda x, y, z: Vector((x, y, z))
# name: (head, tail, parent, connected)
knee = (J[19] + J[20]) * 0.5            # between the two skin joints at the knee
knee.y -= 0.012                          # tiny forward bend so IK knows which way the knee goes
L_BONES = {
    "shoulder.L":  (v(0.025, 0.0, 1.31), J[10], "chest", False),
    "upper_arm.L": (J[10], J[12], "shoulder.L", True),
    "forearm.L":   (J[12], J[14], "upper_arm.L", True),
    "hand.L":      (J[14], J[16], "forearm.L", True),
    "thigh.L":     (J[17], knee, "hips", False),
    "shin.L":      (knee, J[22], "thigh.L", True),
    "foot.L":      (J[22], J[23], "shin.L", True),
    "toe.L":       (J[23], v(J[24].x, -0.22, J[24].z), "foot.L", True),
}
CENTER = {
    "hips":  (J[0], J[2], None, False),
    "spine": (J[2], J[4], "hips", True),
    "chest": (J[4], J[7], "spine", True),
    "neck":  (J[7], J[8], "chest", True),
    "head":  (J[8], v(0.0, J[8].y, 1.72), "neck", True),
}


def mirror(name, spec):
    h, t, p, c = spec
    mx = lambda q: Vector((-q.x, q.y, q.z))
    return name.replace(".L", ".R"), (mx(h), mx(t), p.replace(".L", ".R") if p else None, c)


ALL = dict(CENTER)
ALL.update(L_BONES)
ALL.update(dict(mirror(n, s) for n, s in L_BONES.items()))
ORDER = ["hips", "spine", "chest", "neck", "head",
         "shoulder.L", "upper_arm.L", "forearm.L", "hand.L",
         "shoulder.R", "upper_arm.R", "forearm.R", "hand.R",
         "thigh.L", "shin.L", "foot.L", "toe.L",
         "thigh.R", "shin.R", "foot.R", "toe.R"]
# finger bones from the new hands; the hand bone now ends at the middle knuckle
ROLL = {}
for side, bl in HAND_BONES.items():
    for name, h, t, p, c in bl:
        if name == "HAND_TAIL":
            hh, _, hp, hc = ALL[f"hand.{side}"]
            ALL[f"hand.{side}"] = (hh, h, hp, hc)
            continue
        ALL[name] = (h, t, p, c)
        ORDER.append(name)
        ROLL[name] = PALM_DIR[side]        # local Z toward the palm: +X rotation curls the finger

bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
for name in ORDER:
    h, t, p, c = ALL[name]
    b = eb.new(name)
    b.head, b.tail = h, t
    # local Z points to the character's front (toes point forward already, so their Z points up)
    b.align_roll(ROLL.get(name) or (Vector((0, 0, 1)) if name.startswith("toe") else Vector((0, -1, 0))))
    if p:
        b.parent = eb[p]
        b.use_connect = c
    b.use_deform = True
bpy.ops.object.mode_set(mode='OBJECT')
for b in arm_data.bones:
    print(f"  {b.name:12s} head={tuple(round(x,3) for x in b.head_local)} tail={tuple(round(x,3) for x in b.tail_local)} parent={b.parent.name if b.parent else '-'}")

# ---------------------------------------------------------------------------
# STEP 3 - Skin the mesh to the bones
# ---------------------------------------------------------------------------
print("STEP 3: skinning")
BONES = [b.name for b in arm_data.bones]


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


# 3a. Body: automatic (bone heat) weights, mirrored left/right
for o in bpy.context.selected_objects:
    o.select_set(False)
body.select_set(True)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
with bpy.context.temp_override(active_object=rig, object=rig, selected_objects=[body, rig],
                               selected_editable_objects=[body, rig]):
    bpy.ops.object.parent_set(type='ARMATURE_AUTO', xmirror=True)
arm_mods = [m for m in body.modifiers if m.type == 'ARMATURE']
if not arm_mods:
    add_armature_mod(body)
else:
    with ctx(body):
        bpy.ops.object.modifier_move_to_index(modifier=arm_mods[0].name, index=0)
# fingers belong to the Hands mesh only: give any finger weight on the body to the hand bone
for side in ("L", "R"):
    hand_vg = body.vertex_groups.get(f"hand.{side}") or body.vertex_groups.new(name=f"hand.{side}")
    for vg in [g for g in body.vertex_groups
               if g.name.endswith(f".{side}") and g.name.split(".")[0] in ("thumb", "index", "middle", "ring", "pinky")]:
        for vert in body.data.vertices:
            for g in vert.groups:
                if g.group == vg.index and g.weight > 0:
                    hand_vg.add([vert.index], g.weight, 'ADD')
        body.vertex_groups.remove(vg)
print("  Body groups:", sorted(g.name for g in body.vertex_groups))
print("  Body unweighted verts:", clean_weights(body))

# Hands: weights were painted while building them (rings between two bones share 50/50)
print("  Hands unweighted verts:", clean_weights(hands))
add_armature_mod(hands)

# 3b. Head, hair, cap, eyes...: 100% head bone (rigid)
for ob in char_meshes:
    if ob.name in HEAD_RIGID:
        vg = ob.vertex_groups.new(name="head")
        vg.add([vv.index for vv in ob.data.vertices], 1.0, 'REPLACE')
        add_armature_mod(ob)

# 3c. Clothes: copy weights from the body (nearest face, interpolated)
for ob in CLOTHES:
    for bn in BONES:
        ob.vertex_groups.new(name=bn)
    dt = ob.modifiers.new("WeightCopy", 'DATA_TRANSFER')
    dt.object = body
    dt.use_object_transform = True
    dt.use_vert_data = True
    dt.data_types_verts = {'VGROUP_WEIGHTS'}
    dt.vert_mapping = 'POLYINTERP_NEAREST'
    dt.layers_vgroup_select_src = 'ALL'
    dt.layers_vgroup_select_dst = 'NAME'
    with ctx(ob):
        bpy.ops.object.modifier_move_to_index(modifier=dt.name, index=0)
        bpy.ops.object.modifier_apply(modifier=dt.name)
    empty = clean_weights(ob)
    # drop groups nothing uses, so the list stays tidy
    used = {g.group for vert in ob.data.vertices for g in vert.groups}
    for vg in [vg for vg in ob.vertex_groups if vg.index not in used]:
        ob.vertex_groups.remove(vg)
    add_armature_mod(ob)
    print(f"  {ob.name:18s} groups={len(ob.vertex_groups):2d} unweighted={empty}")

# ---------------------------------------------------------------------------
# STEP 4 - Leg IK (move the red foot bone, the leg bends by itself)
# ---------------------------------------------------------------------------
print("STEP 4: leg IK")
bpy.context.view_layer.objects.active = rig
bpy.ops.object.mode_set(mode='EDIT')
eb = arm_data.edit_bones
for s in ("L", "R"):
    foot, shin = eb[f"foot.{s}"], eb[f"shin.{s}"]
    ik = eb.new(f"IK_foot.{s}")              # copy of the foot, no parent, not deforming
    ik.head, ik.tail, ik.roll = foot.head.copy(), foot.tail.copy(), foot.roll
    ik.use_deform = False
    pole = eb.new(f"pole_knee.{s}")          # in front of the knee: tells the knee where to point
    out = 0.05 if s == "L" else -0.05        # a little outward so the knees never turn in
    pole.head = shin.head + Vector((out, -0.45, 0))
    pole.tail = pole.head + Vector((0, -0.08, 0))
    pole.use_deform = False
bpy.ops.object.mode_set(mode='OBJECT')

# bone collections so you can hide the deform bones while animating
deform_coll = arm_data.collections.new("Deform")
ctrl_coll = arm_data.collections.new("Controls")
for b in arm_data.bones:
    if b.use_deform:
        deform_coll.assign(b)
    else:
        ctrl_coll.assign(b)
        b.color.palette = 'THEME01' if b.name.startswith("IK_") else 'THEME09'   # red / yellow


def leg_error(s):
    err = 0.0
    for n in (f"thigh.{s}", f"shin.{s}"):
        pb, bone = rig.pose.bones[n], arm_data.bones[n]
        err += pb.matrix.to_quaternion().rotation_difference(bone.matrix_local.to_quaternion()).angle
    return err


import math
for s in ("L", "R"):
    pb = rig.pose.bones[f"shin.{s}"]
    ik = pb.constraints.new('IK')
    ik.target, ik.subtarget = rig, f"IK_foot.{s}"
    ik.pole_target, ik.pole_subtarget = rig, f"pole_knee.{s}"
    ik.chain_count = 2
    # find the pole angle that keeps the leg exactly in its rest pose
    best = (1e9, 0.0)
    for step in (10.0, 1.0, 0.1):
        lo, hi = (-180.0, 180.0) if step == 10.0 else (best[1] - step * 10, best[1] + step * 10)
        a = lo
        while a <= hi:
            ik.pole_angle = math.radians(a)
            bpy.context.view_layer.update()
            e = leg_error(s)
            if e < best[0]:
                best = (e, a)
            a += step
    ik.pole_angle = math.radians(best[1])
    cr = rig.pose.bones[f"foot.{s}"].constraints.new('COPY_ROTATION')
    cr.target, cr.subtarget = rig, f"IK_foot.{s}"
    bpy.context.view_layer.update()
    print(f"  shin.{s}: IK chain 2, pole angle {best[1]:.1f} deg, rest error {math.degrees(leg_error(s)):.3f} deg")

# leave the file in a friendly state: rig selected, Pose Mode ready
for o in bpy.context.selected_objects:
    o.select_set(False)
rig.select_set(True)
bpy.context.view_layer.objects.active = rig
arm_data.pose_position = 'POSE'

bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED", OUT)
