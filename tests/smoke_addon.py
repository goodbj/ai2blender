"""Headless smoke test for the MCP for Blender addon command layer.

`BlenderMCPServer.start()` refuses to run under `blender -b` because it depends
on bpy.app.timers firing on the main thread. The socket *protocol* layer does
not need that, so this drives `execute_command()` directly to prove the addon's
command handlers work on Blender 5.2 before we ever open a GUI.
"""
import json
import os
import sys
import traceback

import bpy

ADDON_DIR = os.path.join(
    os.environ["APPDATA"], "Blender Foundation", "Blender", "5.2", "scripts", "addons"
)
ADDON_FILE = os.path.join(ADDON_DIR, "blender_mcp.py")

# Load the addon as a plain module rather than enabling it through the addon
# system, so the test does not depend on preferences or the sidebar panel.
import importlib.util

spec = importlib.util.spec_from_file_location("blender_mcp_under_test", ADDON_FILE)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

print("BLENDER:", bpy.app.version_string)
print("ADDON_PROTOCOL_VERSION:", mod.ADDON_PROTOCOL_VERSION)

server = mod.BlenderMCPServer()

results = []


def run(cmd_type, params=None):
    command = {"type": cmd_type, "params": params or {}}
    try:
        resp = server.execute_command(command)
    except Exception as e:
        resp = {"status": "exception", "message": str(e), "tb": traceback.format_exc()}
    results.append((cmd_type, resp))
    print(f"--- {cmd_type} ---")
    print(json.dumps(resp, indent=2, default=str)[:2500])
    return resp


# 1. liveness / transport check (touches no bpy data)
run("ping")

# 2. scene introspection
run("get_scene_info")

# 3. actual modelling - a primitive
run(
    "execute_blender_code",
    {
        "code": (
            "import bpy\n"
            "bpy.ops.mesh.primitive_uv_sphere_add(radius=1.0, location=(0, 0, 1))\n"
            "obj = bpy.context.active_object\n"
            "obj.name = 'SmokeTestSphere'\n"
            "print('CREATED', obj.name, 'verts=', len(obj.data.vertices))\n"
        )
    },
)

# 4. verify the object really exists
run("get_scene_info")

# 5. modify it - proves bpy state persists across separate commands
run(
    "execute_blender_code",
    {
        "code": (
            "import bpy\n"
            "o = bpy.data.objects.get('SmokeTestSphere')\n"
            "assert o is not None, 'sphere missing'\n"
            "o.scale = (2.0, 2.0, 2.0)\n"
            "print('SCALED', o.name, 'dims=', tuple(round(d,3) for d in o.dimensions))\n"
        )
    },
)

ok = sum(1 for _, r in results if r.get("status") == "success")
print(f"\nSUMMARY: {ok}/{len(results)} commands returned status=success")
print("SCENE OBJECTS:", sorted(o.name for o in bpy.data.objects))
sys.exit(0 if ok == len(results) else 1)
