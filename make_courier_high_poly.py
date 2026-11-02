"""Create a denser, smoother study copy of the Parcel Panic courier scene.

Run this from Blender's Python Console while ParcelPanicCourier_Reference.blend
is open. It keeps the reference file untouched and writes a new .blend file.
"""
import bpy
import os

output_dir = "/Users/joyhowlader/Documents/ChatGPT/final year project/Game/Assets/Characters/ParcelPanicCourier"
os.makedirs(output_dir, exist_ok=True)

for obj in bpy.context.scene.objects:
    if obj.type != 'MESH' or obj.name == "Display ground":
        continue

    # Round the bevels more finely without changing the overall silhouette.
    for mod in obj.modifiers:
        if mod.type == 'BEVEL':
            mod.segments = max(mod.segments, 5)

    # Smooth the deliberately faceted sphere parts, while retaining the shape
    # of boxes and flat props by using simple (non-shrinking) subdivision.
    is_ball = any(tag in obj.name.lower() for tag in (
        "eye", "pupil", "head", "hair", "cap crown", "knee", "ankle",
        "elbow", "hand", "lace"
    ))
    if is_ball:
        sub = obj.modifiers.new("Smooth high-detail form", 'SUBSURF')
        sub.subdivision_type = 'CATMULL_CLARK'
        sub.levels = 2
        sub.render_levels = 2
        for poly in obj.data.polygons:
            poly.use_smooth = True
    else:
        sub = obj.modifiers.new("High-poly surface detail", 'SUBSURF')
        sub.subdivision_type = 'SIMPLE'
        sub.levels = 2
        sub.render_levels = 2

# Keep the scene ready to inspect in Blender and preserve a distinct source file.
bpy.context.scene.render.resolution_percentage = 100
blend_path = os.path.join(output_dir, "ParcelPanicCourier_HighPoly.blend")
bpy.ops.wm.save_as_mainfile(filepath=blend_path)
print("Saved high-poly study copy:", blend_path)
