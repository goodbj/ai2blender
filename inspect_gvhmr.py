import torch

data = torch.load('E:/AI/orca-worktrees/07_AI2Blender/ai2blender/tools/GVHMR/outputs/demo/sample04/hmr4d_results_pp-feet.pt', map_location='cpu')
print('Keys:', data.keys())
for k, v in data.items():
    if hasattr(v, 'shape'):
        print(f'{k}: shape={v.shape}')
    else:
        print(f'{k}: type={type(v)}')
