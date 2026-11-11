"""Step 6 - Export the rigged + animated character to Unity as FBX.

Run:  Blender -b main_character_v012_bag.blend --python export_main_character_fbx.py -- <out.fbx>
      (v012_bag = v011_walk + the backpack from add_backpack.py)

Same settings as File > Export > FBX with:
  Limit to Selected, Armature + Mesh, Apply Scalings = FBX All, Forward -Z, Up Y,
  Apply Transform, Only Deform Bones, no Leaf Bones, Bake Animation (all actions).
"""
import bpy
import os
import sys

OUT = sys.argv[sys.argv.index("--") + 1]
os.makedirs(os.path.dirname(OUT), exist_ok=True)

rig = bpy.data.objects["CourierRig"]
meshes = [o for o in rig.children if o.type == 'MESH']

for o in bpy.context.view_layer.objects:
    o.select_set(False)
for o in [rig] + meshes:
    o.hide_set(False)
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
rig.animation_data.action = bpy.data.actions["Walk"]

# materials: FBX only carries simple colours, so warn about anything fancier
for m in sorted({s.material for o in meshes for s in o.material_slots if s.material}, key=lambda m: m.name):
    tex = [n for n in (m.node_tree.nodes if m.use_nodes else []) if n.type == 'TEX_IMAGE']
    if tex:
        print(f"  material {m.name}: image textures {[n.image.name for n in tex if n.image]}")

bpy.ops.export_scene.fbx(
    filepath=OUT,
    use_selection=True,
    object_types={'ARMATURE', 'MESH'},
    apply_scale_options='FBX_SCALE_ALL',
    axis_forward='-Z',
    axis_up='Y',
    bake_space_transform=True,
    use_mesh_modifiers=True,
    mesh_smooth_type='FACE',
    use_tspace=False,
    add_leaf_bones=False,
    use_armature_deform_only=True,
    armature_nodetype='NULL',
    bake_anim=True,
    bake_anim_use_all_bones=True,
    bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=True,
    bake_anim_force_startend_keying=True,
    bake_anim_step=1.0,
    bake_anim_simplify_factor=0.0,
    path_mode='AUTO',
    embed_textures=False,
)
tris = 0
dg = bpy.context.evaluated_depsgraph_get()
for o in meshes:
    me = o.evaluated_get(dg).to_mesh()
    tris += sum(len(p.vertices) - 2 for p in me.polygons)
    o.evaluated_get(dg).to_mesh_clear()
print(f"EXPORTED {OUT}  meshes={len(meshes)}  triangles={tris}  size={os.path.getsize(OUT)/1e6:.1f} MB")
