"""Step 5 - Walk cycle (+ a small Idle) for the rigged main character.

Run:  Blender -b main_character_v010_rig.blend --python animate_main_character.py -- <out.blend>

The walk is IN PLACE: a foot on the ground moves backwards at exactly the walk
speed, and Unity moves the character forward with code at that same speed, so
the feet stick to the ground. Every frame is calculated from smooth gait curves
(heel strike -> flat foot -> heel lift -> toe push-off -> swing) instead of
being in-betweened from 8 key poses, which is what made the old feet slide.

Change the STYLE numbers below to change how he walks, then run the script again.
"""
import bpy
import math
import sys
from mathutils import Matrix, Vector, Euler

OUT = sys.argv[sys.argv.index("--") + 1]

# ---------------------------------------------------------------------------
# STYLE - the knobs
# ---------------------------------------------------------------------------
FPS = 24
CYCLE = 24              # frames for 2 steps (one loop)
STEP_LENGTH = 0.56      # metres per step
STANCE = 0.62           # part of the loop each foot is on the ground
BOUNCE = 0.020          # hips up/down (metres each way, the legs may limit it)
HIP_SWAY = 0.020        # hips shift over the standing leg (metres)
HIP_TWIST = 7.0         # hips turn with the legs (degrees)
HIP_TILT = 4.0          # free-leg side of the hips drops (degrees)
LEAN = 4.0              # forward lean of the body (degrees)
HEEL_STRIKE = 20.0      # toes up when the heel lands (degrees)
TOE_OFF = 55.0          # heel up when the toes push off (degrees)
FOOT_LIFT = 0.075       # extra lift of the swinging foot (metres)
ARM_SWING = 20.0        # arms forward/back (degrees)
ARM_DRAG = 0.06         # how late forearm and hand follow the upper arm (part of a loop)
FEET_IN = 0.025         # walk with the feet a bit closer than the rest pose

WALK_SPEED = STEP_LENGTH * 2 / (CYCLE / FPS)      # metres per second
MAX_LEG = 0.722         # hip-to-ankle reach we allow (leg is 0.733 straight)

rig = bpy.data.objects["CourierRig"]
P = rig.pose.bones
B = rig.data.bones
for pb in P:
    pb.rotation_mode = 'QUATERNION'

# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------
TAU = 2 * math.pi
R = math.radians


def about(pivot, rot):
    """Rotation `rot` applied around world point `pivot`."""
    return Matrix.Translation(pivot) @ rot.to_4x4() @ Matrix.Translation(-pivot)


def rest(name):
    return B[name].matrix_local.copy()


def ss(x):
    """Smoothstep 0..1."""
    x = min(max(x, 0.0), 1.0)
    return x * x * (3 - 2 * x)


def hermite(p0, p1, m0, m1, u):
    u2, u3 = u * u, u * u * u
    return (2 * u3 - 3 * u2 + 1) * p0 + (u3 - 2 * u2 + u) * m0 + (-2 * u3 + 3 * u2) * p1 + (u3 - u2) * m1


V = STEP_LENGTH * 2                      # ground travel per loop (metres)
ANKLE = B["foot.L"].head_local.copy()    # rest ankle (left)
BALL_Y = B["foot.L"].tail_local.y        # ball of the foot (toe joint)
BALL_Z = B["foot.L"].tail_local.z
HEEL_Y = 0.10                            # back of the shoe on the ground


# ---------------------------------------------------------------------------
# FEET: stance (on the ground) and swing (in the air), phase 0..1, 0 = heel strike
# ---------------------------------------------------------------------------
def stance(ph):
    """Foot on the ground. Returns (ankle y, ankle z, pitch deg, toe deg). pitch > 0 = heel up."""
    dy = V * (ph - STANCE / 2)                     # flat-foot position slides back at walk speed
    if ph < 0.10:                                  # heel rocker: toes come down
        pitch = -HEEL_STRIKE * math.cos(0.5 * math.pi * ph / 0.10)
        toe = 8 * (1 - ss(ph / 0.10))
    elif ph < 0.30:                                # flat foot
        pitch, toe = 0.0, 0.0
    else:                                          # heel lifts, toes stay planted
        k = (ph - 0.30) / (STANCE - 0.30)
        pitch = TOE_OFF * k * k
        toe = pitch
    th = R(pitch)
    # heel down: roll over the back of the heel; heel up: hinge at the ball joint (toes stay flat)
    pivot = Vector((0, BALL_Y + dy, BALL_Z)) if th >= 0 else Vector((0, HEEL_Y + dy, 0.0))
    rel = Matrix.Rotation(th, 3, 'X') @ (Vector((0, ANKLE.y + dy, ANKLE.z)) - pivot)
    return pivot.y + rel.y, pivot.z + rel.z, pitch, toe


def spline(points, u):
    """Smooth curve through (u, value) points, flat at both ends."""
    n = len(points)
    for i in range(n - 1):
        (u0, y0), (u1, y1) = points[i], points[i + 1]
        if u <= u1 or i == n - 2:
            m0 = 0.0 if i == 0 else (y1 - points[i - 1][1]) / (u1 - points[i - 1][0])
            m1 = 0.0 if i == n - 2 else (points[i + 2][1] - y0) / (points[i + 2][0] - u0)
            h = u1 - u0
            return hermite(y0, y1, m0 * h, m1 * h, (u - u0) / h)


# swing: how the foot points while it travels forward (u = 0 toe-off ... 1 heel strike)
SWING_PITCH = [(0.0, TOE_OFF), (0.30, 16.0), (0.65, -4.0), (1.0, -HEEL_STRIKE)]


def foot_state(ph):
    ph %= 1.0
    if ph <= STANCE:
        return stance(ph)
    # swing: smooth curve from toe-off to the next heel strike, speeds matched at both ends
    T = 1.0 - STANCE
    u = (ph - STANCE) / T
    a, b = stance(STANCE), stance(0.0)
    e = 1e-3
    da = [(x - y) / e * T for x, y in zip(stance(STANCE), stance(STANCE - e))]
    db = [(x - y) / e * T for x, y in zip(stance(e), stance(0.0))]
    y = hermite(a[0], b[0], da[0], db[0], u)
    z = hermite(a[1], b[1], da[1], db[1], u) + FOOT_LIFT * math.sin(math.pi * u ** 0.7) ** 2
    pitch = spline(SWING_PITCH, u)
    toe = TOE_OFF * (1 - ss(u / 0.45)) + 8 * ss((u - 0.55) / 0.45)    # toes un-bend as the foot swings
    return y, z, pitch, toe


def foot_matrix(side, ph):
    y, z, pitch, toe = foot_state(ph)
    sx = 1 if side == "L" else -1
    a_rest = B[f"IK_foot.{side}"].head_local
    a = Vector((a_rest.x - sx * FEET_IN, y, z))
    m = Matrix.Translation(a) @ Matrix.Rotation(R(pitch), 4, 'X') @ Matrix.Translation(-a_rest) @ rest(f"IK_foot.{side}")
    return m, toe, ph % 1.0 <= STANCE


# ---------------------------------------------------------------------------
# BODY
# ---------------------------------------------------------------------------
def hips_matrix(t, dz):
    sway = HIP_SWAY * math.sin(TAU * (t - 0.05))           # over the left foot at mid stance
    surge = 0.006 * math.sin(2 * TAU * (t - 0.05))         # body slows at contact, catches up after
    yaw = R(-HIP_TWIST) * math.cos(TAU * (t - 0.02))       # left hip forward with the left leg
    roll = R(-HIP_TILT) * math.sin(TAU * (t - 0.05))       # free-leg side drops
    rot = Matrix.Rotation(yaw, 3, 'Z') @ Matrix.Rotation(roll, 3, 'Y')
    return Matrix.Translation((sway, -surge, dz)) @ about(B["hips"].head_local, rot) @ rest("hips"), yaw, roll


def hip_limit(t):
    """Highest the hips may go this frame so a foot on the ground is still reachable."""
    m, _, _ = hips_matrix(t, 0.0)
    lim = 1.0
    for side, ph in (("L", t), ("R", t + 0.5)):
        fm, _, planted = foot_matrix(side, ph)
        if not planted:
            continue
        hip = m @ (rest("hips").inverted() @ B[f"thigh.{side}"].head_local)
        ank = fm.translation
        horiz = (Vector((hip.x, hip.y)) - Vector((ank.x, ank.y))).length
        lim = min(lim, ank.z + math.sqrt(max(MAX_LEG ** 2 - horiz ** 2, 0.0)) - hip.z)
    return lim


# hips height for every frame: wanted bounce, limited by leg reach, then smoothed
N = CYCLE
want = [-0.030 + BOUNCE * math.cos(2 * TAU * (f / N - 0.34)) for f in range(N)]   # low just after contact
limit = [hip_limit(f / N) for f in range(N)]
dz = [min(w, l) for w, l in zip(want, limit)]
for _ in range(3):
    dz = [(dz[(i - 1) % N] + 2 * dz[i] + dz[(i + 1) % N]) / 4 for i in range(N)]
dz = [min(d, l) for d, l in zip(dz, limit)]


FINGER_NAMES = ("thumb", "index", "middle", "ring", "pinky")
HAS_FINGERS = "index.01.L" in P
# relaxed hand: each finger curls a little more than the one before it (degrees per joint)
RELAXED = {"index": (12, 18, 10), "middle": (16, 22, 12), "ring": (20, 25, 14), "pinky": (24, 28, 16)}


def thumb_tuck_sign(side):
    """Which way round local Z brings the thumb in toward the index finger."""
    pb, idx = P[f"thumb.01.{side}"], B[f"index.01.{side}"]
    target = (idx.tail_local - idx.head_local).normalized()
    best = None
    for sgn in (1, -1):
        pb.rotation_quaternion = Euler((0, 0, R(20 * sgn))).to_quaternion()
        bpy.context.view_layer.update()
        ang = (pb.tail - pb.head).normalized().angle(target)
        if best is None or ang < best[0]:
            best = (ang, sgn)
    pb.rotation_quaternion = (1, 0, 0, 0)
    return best[1]


TUCK = {s: thumb_tuck_sign(s) for s in ("L", "R")} if HAS_FINGERS else {}


def set_fingers(extra=0.0, side_extra=None):
    """Relaxed curl (+X curls toward the palm). `extra` adds a few degrees to every joint."""
    if not HAS_FINGERS:
        return
    for side in ("L", "R"):
        e = extra + (side_extra or {}).get(side, 0.0)
        for f, angles in RELAXED.items():
            for i, a in enumerate(angles, 1):
                P[f"{f}.0{i}.{side}"].rotation_quaternion = Euler((R(a + e), 0, 0)).to_quaternion()
        P[f"thumb.01.{side}"].rotation_quaternion = Euler((R(10 + e), 0, R(24 * TUCK[side]))).to_quaternion()
        P[f"thumb.02.{side}"].rotation_quaternion = Euler((R(12 + e), 0, 0)).to_quaternion()
        P[f"thumb.03.{side}"].rotation_quaternion = Euler((R(16 + e), 0, 0)).to_quaternion()


def set_walk_pose(f):
    t = f / N
    # feet and toes
    for side, ph in (("L", t), ("R", t + 0.5)):
        m, toe, _ = foot_matrix(side, ph)
        P[f"IK_foot.{side}"].matrix = m
        P[f"toe.{side}"].rotation_quaternion = Euler((R(toe), 0, 0)).to_quaternion()

    # hips
    hm, yaw, roll = hips_matrix(t, dz[f % N])
    P["hips"].matrix = hm
    yaw_d, roll_d = math.degrees(yaw), math.degrees(roll)

    # spine and chest twist against the hips; head stays looking ahead
    down = -math.cos(2 * TAU * (t - 0.30))                  # +1 at the low point of the bounce
    lean = LEAN + 1.2 * down
    P["spine"].rotation_quaternion = Euler((R(lean * 0.6), R(-0.75 * yaw_d), R(0.6 * roll_d))).to_quaternion()
    P["chest"].rotation_quaternion = Euler((R(lean * 0.4), R(-0.75 * yaw_d), R(0.6 * roll_d))).to_quaternion()
    P["neck"].rotation_quaternion = Euler((R(-lean * 0.4), R(0.25 * yaw_d), R(-0.1 * roll_d))).to_quaternion()
    nod = 1.0 * math.cos(2 * TAU * (t - 0.12))              # small nod just after each landing
    P["head"].rotation_quaternion = Euler((R(-lean * 0.5 - nod), R(0.25 * yaw_d), R(-0.1 * roll_d))).to_quaternion()

    # arms: opposite to the legs; forearm and hand drag behind (overlapping action)
    lift = math.sin(TAU * (t - 0.05))
    hand_extra = {}
    for side, sgn, zs in (("L", -1, -1), ("R", 1, 1)):
        upper = 3 + ARM_SWING * sgn * math.cos(TAU * (t - 0.03))              # + = forward
        fore = 14 + 9 * sgn * math.cos(TAU * (t - 0.03 - ARM_DRAG))           # bends more when forward
        hand = 3 + 7 * sgn * math.sin(TAU * (t - 0.03 - ARM_DRAG * 1.5))      # wrist flops behind the swing
        P[f"upper_arm.{side}"].rotation_quaternion = Euler((R(upper), 0, R(zs * 7))).to_quaternion()
        P[f"forearm.{side}"].rotation_quaternion = Euler((R(fore), 0, 0)).to_quaternion()
        P[f"hand.{side}"].rotation_quaternion = Euler((R(hand), 0, 0)).to_quaternion()
        # shoulders: the one over the standing leg drops a little
        P[f"shoulder.{side}"].rotation_quaternion = Euler((0, 0, R(zs * -1.5 * lift * -sgn))).to_quaternion()
        hand_extra[side] = 2 * sgn * math.sin(TAU * (t - 0.03 - ARM_DRAG * 2))
    set_fingers(extra=2.0, side_extra=hand_extra)


ANIM_BONES = ["hips", "spine", "chest", "neck", "head",
              "IK_foot.L", "IK_foot.R", "toe.L", "toe.R",
              "shoulder.L", "upper_arm.L", "forearm.L", "hand.L",
              "shoulder.R", "upper_arm.R", "forearm.R", "hand.R"]
if HAS_FINGERS:
    ANIM_BONES += [f"{f}.0{i}.{s}" for s in ("L", "R") for f in FINGER_NAMES for i in (1, 2, 3)]


def key_all(frame):
    for n in ANIM_BONES:
        pb = P[n]
        if n in ("hips", "IK_foot.L", "IK_foot.R"):
            pb.keyframe_insert("location", frame=frame, group=n)
        pb.keyframe_insert("rotation_quaternion", frame=frame, group=n)


def reset_pose():
    for pb in P:
        pb.location = (0, 0, 0)
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.scale = (1, 1, 1)


def fcurves_of(action):
    """Blender 4.4+ (slotted actions) and older versions."""
    try:
        from bpy_extras import anim_utils
        slot = rig.animation_data.action_slot
        bag = anim_utils.action_get_channelbag_for_slot(action, slot)
        return list(bag.fcurves) if bag else []
    except Exception:
        return list(action.fcurves)


def make_cyclic(action):
    for fc in fcurves_of(action):
        if not any(m.type == 'CYCLES' for m in fc.modifiers):
            fc.modifiers.new('CYCLES')
        fc.update()


def new_action(name):
    old = bpy.data.actions.get(name)
    if old:
        bpy.data.actions.remove(old)
    act = bpy.data.actions.new(name)
    act.use_fake_user = True            # the shield: Blender keeps it even if unused
    rig.animation_data_create()
    rig.animation_data.action = act
    return act


# ---------------------------------------------------------------------------
# WALK: a key on every frame, frame 25 = frame 1 so it loops
# ---------------------------------------------------------------------------
walk = new_action("Walk")
reset_pose()
for f in range(N + 1):
    set_walk_pose(f % N)
    key_all(1 + f)
make_cyclic(walk)
walk.use_frame_range = True
walk.frame_start, walk.frame_end = 1, 1 + CYCLE
walk.use_cyclic = True
# markers so the classic key poses are easy to find in the timeline
sc = bpy.context.scene
for m in list(sc.timeline_markers):
    sc.timeline_markers.remove(m)
half = N // 2
low = min(range(half), key=lambda i: dz[i])                       # lowest hips
high = max(range(half), key=lambda i: dz[i])                      # highest hips
toe_off = round(((STANCE - 0.5) % 1.0) * N)                       # back foot leaves the ground
passing = min(range(half), key=lambda i: abs(foot_state(i / N + 0.5)[0] - foot_state(i / N)[0])
              if foot_state(i / N + 0.5)[1] > ANKLE.z + 0.02 else 9)
for i, label in ((0, "Contact"), (low, "Down"), (toe_off, "Toe-off"), (passing, "Passing"), (high, "Up")):
    sc.timeline_markers.new(f"{label} L", frame=1 + i)
    sc.timeline_markers.new(f"{label} R", frame=1 + i + half)
print("KEY POSES (frame): contact 1, down", 1 + low, "toe-off", 1 + toe_off, "passing", 1 + passing, "up", 1 + high)

# ---------------------------------------------------------------------------
# IDLE: 2 second breathing loop, arms relaxed
# ---------------------------------------------------------------------------
idle = new_action("Idle")
reset_pose()
IDLE_LEN = 48
for i, f in enumerate((1, 13, 25, 37, 49)):
    ph = TAU * i / 4                         # one breath per loop
    br = math.sin(ph)                        # -1..1
    P["hips"].matrix = Matrix.Translation((0.004 * math.sin(ph / 2 if i < 4 else 0), 0, -0.012 + 0.004 * br)) @ rest("hips")
    P["spine"].rotation_quaternion = Euler((R(1.0), 0, 0)).to_quaternion()
    P["chest"].rotation_quaternion = Euler((R(-1.2 * br), 0, 0)).to_quaternion()
    P["head"].rotation_quaternion = Euler((R(0.8 * br), R(1.5 * math.sin(ph / 2 if i < 4 else 0)), 0)).to_quaternion()
    for side, zs in (("L", -1), ("R", 1)):
        P[f"shoulder.{side}"].rotation_quaternion = Euler((0, 0, zs * R(-1.0 * br))).to_quaternion()
        P[f"upper_arm.{side}"].rotation_quaternion = Euler((R(2), 0, zs * R(8 + 1.0 * br))).to_quaternion()
        P[f"forearm.{side}"].rotation_quaternion = Euler((R(16 + 2 * br), 0, 0)).to_quaternion()
        P[f"hand.{side}"].rotation_quaternion = Euler((R(5), 0, 0)).to_quaternion()
        P[f"IK_foot.{side}"].matrix = rest(f"IK_foot.{side}")
    set_fingers(extra=2 * br)
    key_all(f)
make_cyclic(idle)
idle.use_frame_range = True
idle.frame_start, idle.frame_end = 1, 1 + IDLE_LEN
idle.use_cyclic = True

# ---------------------------------------------------------------------------
# scene: show the walk, loop frames 1-24
# ---------------------------------------------------------------------------
rig.animation_data.action = walk
sc.render.fps = FPS
sc.frame_start, sc.frame_end = 1, CYCLE
sc.frame_set(1)
print(f"HIPS dz per frame (cm): {' '.join(f'{d*100:.1f}' for d in dz)}")
print(f"WALK speed {WALK_SPEED:.3f} m/s  (set this as walkAnimationSpeed in Unity)")
bpy.ops.wm.save_as_mainfile(filepath=OUT, compress=True)
print("SAVED", OUT)
