import torch

data = torch.load('E:/AI/orca-worktrees/07_AI2Blender/ai2blender/tools/GVHMR/outputs/demo/sample04/hmr4d_results_pp-feet.pt', map_location='cpu')
print('smpl_params_global keys:', data['smpl_params_global'].keys())
for k, v in data['smpl_params_global'].items():
    if hasattr(v, 'shape'):
        print(f'{k}: shape={v.shape}')
    else:
        print(f'{k}: type={type(v)}')
