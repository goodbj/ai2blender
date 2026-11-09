"""
GVHMR 输出 → SMPLX mesh 序列导出（绕开 pytorch3d）
读取 hmr4d_results_pp-feet.pt（140帧 SMPLX 参数）
用 smplx 逐帧生成 mesh 顶点 + faces + 关节位置，存为 NPZ 供 Blender 加载。

用法：
    .\.venv\Scripts\python.exe gvhmr_to_smplx_seq.py --input-pt <path>.pt --output-npz <path>.npz [--fps 30]
"""
import argparse
import torch
import numpy as np
from pathlib import Path
from smplx import SMPLXLayer
from pytorch3d.transforms import axis_angle_to_matrix

GVHMR_ROOT = Path(r"E:/AI/orca-worktrees/07_AI2Blender/ai2blender/tools/GVHMR")
SMPLX_DIR = GVHMR_ROOT / "inputs/checkpoints/body_models/smplx"


def main():
    ap = argparse.ArgumentParser(description="GVHMR .pt -> smplx mesh sequence .npz")
    ap.add_argument("--input-pt", required=True, help="GVHMR hmr4d_results_pp-feet.pt 路径")
    ap.add_argument("--output-npz", required=True, help="输出 NPZ 路径")
    ap.add_argument("--fps", type=int, default=30, help="帧率，默认 30")
    args = ap.parse_args()

    pt_path = Path(args.input_pt)
    out_path = Path(args.output_npz)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # ---- 1. 读取 GVHMR 输出 ----
    print(f"[1/4] 读取 {pt_path}")
    data = torch.load(pt_path, map_location="cpu")
    sp = data["smpl_params_global"]  # body_pose[*,63] betas[*,10] global_orient[*,3] transl[*,3]
    nf = sp["body_pose"].shape[0]
    print(f"    帧数 = {nf}")

    # ---- 2. 加载 SMPLX 模型（neutral, 10 betas） ----
    print("[2/4] 加载 SMPLX 模型")
    model = SMPLXLayer(
        model_path=str(SMPLX_DIR),
        gender="neutral",
        num_betas=10,
        num_expression=10,
        use_pca=False,
        flat_hand_mean=False,
    )

    # ---- 3. 逐帧前向，收集 vertices / joints / faces ----
    print("[3/4] 逐帧生成 mesh")
    all_verts = []
    all_joints = []
    faces = None
    with torch.no_grad():
        for i in range(nf):
            out = model(
                global_orient=axis_angle_to_matrix(sp["global_orient"][i:i+1]),
                body_pose=axis_angle_to_matrix(sp["body_pose"][i:i+1].reshape(1, -1, 3)),
                betas=sp["betas"][i:i+1],
                transl=sp["transl"][i:i+1],
                expression=torch.zeros(1, 10),
                jaw_pose=axis_angle_to_matrix(torch.zeros(1, 3)),
                leye_pose=axis_angle_to_matrix(torch.zeros(1, 3)),
                reye_pose=axis_angle_to_matrix(torch.zeros(1, 3)),
                left_hand_pose=axis_angle_to_matrix(torch.zeros(1, 15, 3)),
                right_hand_pose=axis_angle_to_matrix(torch.zeros(1, 15, 3)),
            )
            all_verts.append(out.vertices[0].cpu().numpy())
            all_joints.append(out.joints[0].cpu().numpy())
            if faces is None:
                faces = np.asarray(model.faces)

    all_verts = np.stack(all_verts, axis=0)   # (nf, 10475, 3)
    all_joints = np.stack(all_joints, axis=0)  # (nf, 55, 3)
    print(f"    verts shape = {all_verts.shape}, joints shape = {all_joints.shape}, faces = {faces.shape}")

    # ---- 4. 存盘 ----
    print("[4/4] 保存 NPZ")
    lbs_weights = model.lbs_weights.detach().cpu().numpy().astype(np.float32)  # (10475, J)
    parents = model.parents.detach().cpu().numpy().astype(np.int64)  # (J,)
    np.savez(
        out_path,
        vertices=all_verts.astype(np.float32),
        joints=all_joints[:, :55, :].astype(np.float32),
        faces=faces.astype(np.int64),
        lbs_weights=lbs_weights,
        parents=parents,
        fps=np.array(args.fps, dtype=np.int32),
    )
    print(f"    lbs_weights shape = {lbs_weights.shape}")
    print(f"    已保存 -> {out_path}")
    print("DONE")


if __name__ == "__main__":
    main()
