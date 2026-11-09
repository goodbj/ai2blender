"""
Blender headless: 用 smplx NPZ 序列建带骨骼绑定(SMPLX 55关节)的 mesh，导出 FBX。
运行: blender --background --python build_fbx.py --input-npz <npz> --output-fbx <fbx> [--output-blend <blend>]
"""
import argparse
import sys
import os
import numpy as np
import bpy

# ---- SMPLX 55 关节标准命名（与 smplx kintree 顺序一致） ----
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
    # Blender 会把 -- 之后的参数透传给脚本；先剥离，避免被 Blender 自带参数干扰
    argv = sys.argv
    if "--" in argv:
        argv = argv[argv.index("--") + 1:]
    else:
        argv = argv[1:]
    ap = argparse.ArgumentParser(description="smplx NPZ -> Blender rigged FBX")
    ap.add_argument("--input-npz", required=True, help="输入 NPZ 路径")
    ap.add_argument("--output-fbx", required=True, help="输出 FBX 路径")
    ap.add_argument("--output-blend", help="额外保存 .blend 路径（可选）")
    args = ap.parse_args(argv)

    npz = args.input_npz
    out_fbx = args.output_fbx
    out_blend = args.output_blend

    print("[LOAD] NPZ")
    d = np.load(npz)
    verts = d["vertices"].astype(np.float32)   # (nf, 10475, 3)
    joints = d["joints"].astype(np.float32)    # (nf, 55, 3)
    faces = d["faces"].astype(np.int32)        # (nf, 3) -> actually (20908,3)
    weights = d["lbs_weights"].astype(np.float32)  # (10475, 55)
    parents = d["parents"].astype(np.int32)    # (55,)
    nf = verts.shape[0]
    nv = verts.shape[1]
    print(f"  frames={nf} verts={nv} joints={joints.shape[1]} faces={faces.shape[0]}")

    # ---- 清理场景 ----
    bpy.ops.wm.read_factory_settings(use_empty=True)

    # ---- 建 mesh ----
    mesh = bpy.data.meshes.new("GVHMR_Mesh")
    obj = bpy.data.objects.new("GVHMR_Body", mesh)
    bpy.context.collection.objects.link(obj)

    # 顶点/面（用第一帧 bind pose）
    co = verts[0].reshape(-1, 3)
    mesh.from_pydata(co.tolist(), [], faces.tolist())
    mesh.update()

    # ---- 建 armature（SMPLX 55 关节，按 parent 树） ----
    print("[ARMATURE] 建骨骼")
    amt = bpy.data.armatures.new("SMPLX_Armature")
    arm_obj = bpy.data.objects.new("SMPLX_Rig", amt)
    bpy.context.collection.objects.link(arm_obj)
    bpy.context.view_layer.objects.active = arm_obj
    bpy.ops.object.mode_set(mode="EDIT")

    bone_map = {}
    for j in range(joints.shape[1]):
        name = JOINT_NAMES[j] if j < len(JOINT_NAMES) else f"joint_{j}"
        p = parents[j]
        eb = amt.edit_bones.new(name)
        head = joints[0, j].tolist()
        if p >= 0:
            eb.parent = bone_map[p]
            eb.head = bone_map[p].tail
        else:
            eb.head = (head[0], head[1], head[2])
        # tail: 朝第一个子关节，若无子关节则 +Z 偏移 0.1 避免零长骨骼
        child_idx = [c for c in range(joints.shape[1]) if parents[c] == j]
        if child_idx:
            eb.tail = joints[0, child_idx[0]].tolist()
        else:
            eb.tail = (head[0], head[1], head[2] + 0.1)
        bone_map[j] = eb

    bpy.ops.object.mode_set(mode="OBJECT")

    # ---- 骨骼动画：每帧设每根骨骼位置（相对父骨骼的局部平移） ----
    print("[ARMATURE ANIM] 逐帧设关节")
    for f in range(nf):
        for j in range(joints.shape[1]):
            name = JOINT_NAMES[j] if j < len(JOINT_NAMES) else f"joint_{j}"
            pb = arm_obj.pose.bones[name]
            p = parents[j]
            if p >= 0:
                loc = (joints[f, j] - joints[f, p]).tolist()
            else:
                loc = joints[f, j].tolist()
            pb.location = (loc[0], loc[1], loc[2])
        for j in range(joints.shape[1]):
            name = JOINT_NAMES[j] if j < len(JOINT_NAMES) else f"joint_{j}"
            arm_obj.pose.bones[name].keyframe_insert(data_path="location", frame=f + 1)
    arm_action = arm_obj.animation_data.action
    print(f"    action = {arm_action.name if arm_action else None}")

    # ---- 蒙皮：把 mesh 绑定到 armature ----
    print("[SKIN] 绑定权重")
    mod = obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_obj
    for j in range(joints.shape[1]):
        name = JOINT_NAMES[j] if j < len(JOINT_NAMES) else f"joint_{j}"
        obj.vertex_groups.new(name=name)
    for v in range(nv):
        w = weights[v]
        idx = np.argsort(w)[::-1][:4]
        for j in idx:
            if w[j] > 1e-4:
                name = JOINT_NAMES[j] if j < len(JOINT_NAMES) else f"joint_{j}"
                obj.vertex_groups[name].add([v], float(w[j]), "REPLACE")

    # ---- 自检 ----
    print("[SELFCHECK] 骨骼动画关键帧")
    print(f"    action={arm_action.name if arm_action else None} frame_range={tuple(arm_action.frame_range) if arm_action else None}")

    # ---- 导出 FBX ----
    print("[EXPORT] FBX")
    os.makedirs(os.path.dirname(out_fbx), exist_ok=True)
    if out_blend:
        os.makedirs(os.path.dirname(out_blend), exist_ok=True)
        bpy.ops.wm.save_as_mainfile(filepath=out_blend)
    bpy.ops.export_scene.fbx(
        filepath=out_fbx,
        use_selection=False,
        global_scale=1.0,
        add_leaf_bones=False,
        use_armature_deform_only=True,
        bake_anim=True,
        bake_anim_use_all_bones=True,
        bake_anim_step=1.0,
        bake_anim_simplify_factor=0.0,
    )
    print(f"[DONE] 导出 -> {out_fbx}")


if __name__ == "__main__":
    main()
