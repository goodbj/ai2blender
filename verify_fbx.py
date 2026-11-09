"""
验证脚本：导入 FBX 检查骨骼绑定 + 用 render 出 PNG 截图（headless 兼容）。
运行: blender --background --python verify_fbx.py --input-fbx <fbx> --output-shot <png>
"""
import argparse
import sys
import bpy, os

JOINT_NAMES = [
    "pelvis", "left_hip", "right_hip", "spine1", "left_knee", "right_knee",
    "spine2", "left_ankle", "right_ankle", "spine3", "left_foot", "right_foot",
    "neck", "left_collar", "right_collar", "head", "left_shoulder", "right_shoulder",
    "left_elbow", "right_elbow", "left_wrist", "right_wrist",
    "left_index1", "left_index2", "left_index3", "left_middle1", "left_middle2", "left_middle3",
    "left_pinky1", "left_pinky2", "left_pinky3", "left_ring1", "left_ring2", "left_ring3",
    "left_thumb1", "left_thumb2", "left_thumb3", "right_index1", "right_index2", "right_index3",
    "right_middle1", "right_middle2", "right_middle3", "right_pinky1", "right_pinky2", "right_pinky3",
    "right_ring1", "right_ring2", "right_ring3", "right_thumb1", "right_thumb2", "right_thumb3",
    "nose", "right_eye", "left_eye", "right_ear", "left_ear",
]


def main():
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = argv[1:]
    ap = argparse.ArgumentParser(description="验证导入的 FBX 骨骼绑定并出截图")
    ap.add_argument("--input-fbx", required=True, help="待验证的 FBX 路径")
    ap.add_argument("--output-shot", required=True, help="输出截图 PNG 路径")
    args = ap.parse_args(argv)

    fbx = args.input_fbx
    shot = args.output_shot

    bpy.ops.wm.read_factory_settings(use_empty=True)
    print("[IMPORT] FBX")
    bpy.ops.import_scene.fbx(filepath=fbx)

    arm = None
    mesh = None
    for o in bpy.data.objects:
        if o.type == "ARMATURE":
            arm = o
        elif o.type == "MESH":
            mesh = o

    print(f"[CHECK] armature = {arm.name if arm else None}")
    print(f"[CHECK] mesh = {mesh.name if mesh else None}")

    if arm:
        bones = arm.data.bones
        print(f"[CHECK] 骨骼数 = {len(bones)}")
        print(f"[CHECK] 前10根骨骼名 = {[b.name for b in bones[:10]]}")
        n_ok = sum(1 for b in bones if b.name in JOINT_NAMES)
        print(f"[CHECK] 标准命名骨骼数 = {n_ok}/{len(bones)}")

    if mesh:
        print(f"[CHECK] 网格顶点数 = {len(mesh.data.vertices)}")
        print(f"[CHECK] 网格面数 = {len(mesh.data.polygons)}")
        print(f"[CHECK] 顶点组数 = {len(mesh.vertex_groups)}")
        print(f"[CHECK] 修改器 = {[m.type for m in mesh.modifiers]}")

    print("[CHECK] 动画 actions:")
    for act in bpy.data.actions:
        rng = act.frame_range
        n = int(round(rng[1] - rng[0])) + 1 if rng[1] > rng[0] else 0
        print(f"    {act.name}: frame_range=({rng[0]:.0f}, {rng[1]:.0f}) 约 {n} 帧")

    # ---- 用 render 出图（headless 兼容） ----
    print("[RENDER] 渲染验证截图")
    scene = bpy.context.scene
    scene.render.engine = 'BLENDER_EEVEE'
    scene.render.image_settings.file_format = 'PNG'
    scene.render.filepath = shot
    scene.render.resolution_x = 1280
    scene.render.resolution_y = 720
    cam = bpy.data.cameras.new("VerifyCam")
    cam_obj = bpy.data.objects.new("VerifyCam", cam)
    scene.collection.objects.link(cam_obj)
    scene.camera = cam_obj
    if arm:
        arm.location = (0, 0, 0)
        cam_obj.location = (0, -3, 1.5)
        cam_obj.rotation_euler = (1.3, 0, 0)
    light = bpy.data.lights.new("VerifyLight", 'SUN')
    light_obj = bpy.data.objects.new("VerifyLight", light)
    scene.collection.objects.link(light_obj)
    light_obj.location = (2, -2, 5)
    scene.frame_set(70)
    if arm:
        arm.location = (0, 0, 0)
    bpy.ops.render.render(write_still=True)
    print(f"[DONE] 截图(第70帧) -> {shot}")


if __name__ == "__main__":
    main()
