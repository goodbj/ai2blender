worker_done

#178 批量转阶段已全部完成，产出 10 个动作素材并落库，可交付 09/12 部门。

## 已完成
1. **重跑 4 个已处理视频**（样例03/样例04/目标01/目标05）：复用 #177 已验收的 GVHMR 产物，走 smplx→mesh→FBX 管线，FBX+截图全部验收通过（55/55 标准命名骨骼、ARMATURE 蒙皮修改器、动画帧数正确）。
2. **跑通 5 个待转视频**（样例01/样例02/目标02/目标03/客户原片）：先跑 GVHMR 推理生成 hmr4d_results.pt，再 smplx→NPZ→Blender headless→FBX，5 个全部验收通过。
3. **补充第10个动作**：GVHMR 自带 `docs/example_video/tennis.mp4`（网球挥拍），跑管线出 FBX，验证通过。
4. **Blender rigging 调整**：55 根 SMPLX 标准命名骨骼、LBS 蒙皮权重（顶点前4大权重绑定顶点组）、ARMATURE 修改器，骨骼驱动动画（location 关键帧），无骨骼命名/旋转不匹配问题。
5. **导出落库**：10 个素材（.fbx + .blend + 验证截图）已复制到 `E:/AI/AI_Memory/知识库/07-AI2Blender-动捕/素材库/` 下各子目录。
6. **脚本参数化**：`gvhmr_to_smplx_seq.py` / `build_fbx.py` / `verify_fbx.py` 已改为支持 `--input-pt/--output-npz` / `--input-npz/--output-fbx`，后续可批量复用。

## 素材落库列表（10个）
| 序号 | 动作类型 | 视频源 | FBX路径 | 帧数 |
|---|---|---|---|---|
| 1 | 基础 T-pose 静止锚点 | 样例01.mp4 | 素材库/样例01/样例01_gvhmr.fbx | 340 |
| 2 | 手臂挥动/挥手 | 样例02.mp4 | 素材库/样例02/样例02_gvhmr.fbx | 383 |
| 3 | 踢腿动作 | 样例03.mp4 | 素材库/样例03/样例03_gvhmr.fbx | 540 |
| 4 | 弯腰/俯身 | 样例04.mp4 | 素材库/样例04/样例04_gvhmr.fbx | 140 |
| 5 | 跳跃/弹跳 | 目标01.mp4 | 素材库/目标01/目标01_gvhmr.fbx | 263 |
| 6 | 转身/回旋 | 目标02.mp4 | 素材库/目标02/目标02_gvhmr.fbx | 60 |
| 7 | 蹲下/站起 | 目标03.mp4 | 素材库/目标03/目标03_gvhmr.fbx | 51 |
| 8 | 侧步/横移 | 目标05.mp4 | 素材库/目标05/目标05_gvhmr.fbx | 540 |
| 9 | 客户指定动作 | 01客户提供要求做的原片.mp4 | 素材库/客户原片/customer01_gvhmr.fbx | 480 |
| 10 | 第10个动作（网球挥拍） | GVHMR docs/example_video/tennis.mp4 | 素材库/第10个动作_网球挥拍/tennis_gvhmr.fbx | 312 |

验收证据：每个素材目录均含 .fbx、.blend、_verify.png（Blender 导入验证截图）。
