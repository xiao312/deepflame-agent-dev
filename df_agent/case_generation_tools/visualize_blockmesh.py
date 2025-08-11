import json
import os
import base64
import shutil
import subprocess
from pathlib import Path


def _cmd_exists(cmd: str) -> bool:
    """Return True if an executable exists in PATH."""
    return shutil.which(cmd) is not None


def visualize_blockmesh(config_json: str) -> str:
    """
    Run `blockMesh` for a case and return a base64 PNG wireframe preview of the mesh.

    PARAMETERS (single JSON string; MUST confirm with user before calling)
    ---------------------------------------------------------------------
    config_json example:
    {
      "case_path": "output/2D_HIT_template"   // REQUIRED; path containing system/blockMeshDict
    }

    LLM_CALL_CONVENTION
    -------------------
    • Before invoking, the agent MUST echo: case_path and whether `system/blockMeshDict`
      exists; then ask for explicit confirmation ("确认/confirm").

    RETURNS (str, JSON)
    -------------------
      Success:
        {
          "status": "success",
          "report": "Successfully generated mesh and preview.",
          "image_base64": "...",            // PNG (data URI not included)
          "stdout": "..."                    // blockMesh stdout (truncated)
        }
      Error:
        {"status": "error", "error_message": "...", "details": "..."}

    NOTES
    -----
    • Requires OpenFOAM in PATH (`blockMesh`) and Python package `pyvista` (with VTK).
    • Off-screen rendering is used; no GUI required.
    • No files are kept; temporary `.foam` and screenshot are removed after use.
    """
    try:
        data = json.loads(config_json)
        case_path = data.get("case_path")
        if not case_path:
            return json.dumps({"status": "error", "error_message": "Missing required field: case_path"}, ensure_ascii=False)

        case_dir = Path(case_path)
        blockmesh_dict = case_dir / "system" / "blockMeshDict"
        if not blockmesh_dict.is_file():
            return json.dumps({
                "status": "error",
                "error_message": f"blockMeshDict not found at '{blockmesh_dict}'."
            }, ensure_ascii=False)

        # Dependencies
        if not _cmd_exists("blockMesh"):
            return json.dumps({
                "status": "error",
                "error_message": "'blockMesh' not found in PATH. Ensure OpenFOAM environment is sourced."
            }, ensure_ascii=False)

        try:
            import pyvista as pv
            pv.set_plot_theme("document")
            pv.global_theme.off_screen = True if hasattr(pv, 'global_theme') else None
            # Back-compat for older pyvista
            if hasattr(pv, 'global_vars'):
                pv.global_vars.off_screen = True
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error_message": "PyVista is not available. Install with 'pip install pyvista[all] panel'",
                "details": str(e)
            }, ensure_ascii=False)

        # Run blockMesh
        proc = subprocess.run(["blockMesh"], cwd=case_dir, capture_output=True, text=True)
        if proc.returncode != 0:
            return json.dumps({
                "status": "error",
                "error_message": "blockMesh execution failed.",
                "details": proc.stderr
            }, ensure_ascii=False)

        # Prepare a temporary .foam file for VTK reader
        foam_file = case_dir / f"{case_dir.name}.foam"
        try:
            foam_file.touch(exist_ok=True)
        except Exception as e:
            return json.dumps({
                "status": "error",
                "error_message": f"Failed to create temporary .foam file: {e}"
            }, ensure_ascii=False)

        try:
            reader = pv.OpenFOAMReader(str(foam_file))
            mesh = reader.read()

            # Render wireframe
            plotter = pv.Plotter(off_screen=True)
            plotter.add_mesh(mesh, style='wireframe', line_width=2)
            plotter.view_xy()
            plotter.enable_parallel_projection()

            # Save screenshot
            out_png = case_dir / "mesh_visualization.png"
            plotter.screenshot(str(out_png))
            plotter.close()

            with open(out_png, 'rb') as f:
                img_b64 = base64.b64encode(f.read()).decode('utf-8')
        finally:
            # Cleanup temp artifacts
            try:
                if foam_file.exists():
                    foam_file.unlink()
            except Exception:
                pass
            try:
                if 'out_png' in locals() and out_png.exists():
                    out_png.unlink()
            except Exception:
                pass

        # Truncate stdout to keep payload small
        stdout_short = proc.stdout[:2000]

        return json.dumps({
            "status": "success",
            "report": f"Successfully generated mesh for '{case_dir}' and created visualization.",
            "image_base64": img_b64,
            "stdout": stdout_short
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_message": f"Unexpected error during mesh visualization: {e}"
        }, ensure_ascii=False)


if __name__ == "__main__":
    # Smoke test (will only work if OpenFOAM + PyVista are available)
    TEST = "visualize_test_case"
    os.makedirs(os.path.join(TEST, "system"), exist_ok=True)
    os.makedirs(os.path.join(TEST, "constant"), exist_ok=True)

    # Minimal blockMeshDict (unit cube)
    blockmesh = """
FoamFile
{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}
convertToMeters 1;
vertices
(
    (0 0 0)
    (1 0 0)
    (1 1 0)
    (0 1 0)
    (0 0 1)
    (1 0 1)
    (1 1 1)
    (0 1 1)
);
blocks
(
    hex (0 1 2 3 4 5 6 7) (6 6 1) simpleGrading (1 1 1)
);
edges
(
);
boundary
(
    inlet { type patch; faces ((0 4 7 3)); }
    outlet { type patch; faces ((1 2 6 5)); }
    walls { type wall; faces ((0 1 5 4) (2 3 7 6)); }
    frontAndBack { type empty; faces ((0 3 2 1) (4 5 6 7)); }
);
"""
    with open(os.path.join(TEST, "system", "blockMeshDict"), "w", encoding="utf-8") as f:
        f.write(blockmesh)

    cfg = {"case_path": TEST}
    print(visualize_blockmesh(json.dumps(cfg, ensure_ascii=False)))

    # Cleanup (keep folder if you want to inspect)
    import shutil
    shutil.rmtree(TEST, ignore_errors=True)
    print(f"Cleaned up '{TEST}'.")
