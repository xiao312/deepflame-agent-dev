import json
import os
from pathlib import Path
from typing import Any


def _format_vertices(vertices_list: list) -> str:
    """Format the vertices list for blockMeshDict."""
    lines = ["("]
    for v in vertices_list:
        if not (isinstance(v, (list, tuple)) and len(v) == 3):
            raise ValueError(f"Invalid vertex entry: {v}")
        lines.append(f"    ({v[0]} {v[1]} {v[2]})")
    lines.append(");")
    return "\n".join(lines)


def _format_blocks(blocks_list: list) -> str:
    """Format the blocks section for blockMeshDict."""
    lines = ["("]
    for block in blocks_list:
        if not isinstance(block, dict):
            raise ValueError("Each block must be an object/dict")
        hex_idx = block.get("hex")
        cells = block.get("cells")
        grading_type = block.get("grading_type", "simpleGrading")
        grading_val = block.get("grading")
        if hex_idx is None or cells is None or grading_val is None:
            raise ValueError("Block requires 'hex', 'cells', and 'grading'")
        if len(hex_idx) != 8:
            raise ValueError("Block 'hex' must have 8 vertex indices")
        hex_str = " ".join(map(str, hex_idx))
        cells_str = " ".join(map(str, cells))
        lines.append(f"    hex ({hex_str}) ({cells_str})")
        if grading_type == "simpleGrading":
            grading_str = " ".join(map(str, grading_val))
            lines.append(f"    simpleGrading ({grading_str})")
        elif grading_type == "edgeGrading":
            lines.append("    edgeGrading")
            lines.append("    (")
            for edge in grading_val:
                lines.append(f"        {' '.join(map(str, edge))}")
            lines.append("    )")
        else:
            raise ValueError(f"Unsupported grading_type: {grading_type}")
    lines.append(");")
    return "\n".join(lines)


def _format_boundary(patches_list: list) -> str:
    """Format the boundary section for blockMeshDict."""
    lines = ["("]
    for patch in patches_list:
        if not isinstance(patch, dict):
            raise ValueError("Each patch must be an object/dict")
        name = patch.get("name")
        ptype = patch.get("type")
        faces = patch.get("faces")
        if not name or not ptype or not isinstance(faces, list):
            raise ValueError("Patch requires 'name', 'type', and 'faces' array")
        lines.append(f"    {name}")
        lines.append("    {")
        lines.append(f"        type {ptype};")
        lines.append("        faces")
        lines.append("        (")
        for face in faces:
            face_str = " ".join(map(str, face))
            lines.append(f"            ({face_str})")
        lines.append("        );")
        lines.append("    }")
    lines.append(");")
    return "\n".join(lines)


def edit_blockMeshDict(config_json: str) -> str:
    """
    Create or overwrite `system/blockMeshDict` using structured parameters.

    PARAMETERS (single JSON string; MUST confirm with user before calling)
    ---------------------------------------------------------------------
    config_json example:
    {
      "case_path": "output/2D_HIT_template",        // REQUIRED
      "convertToMeters": 1.0,                           // OPTIONAL (default: 1.0)
      "vertices": [                                     // REQUIRED (list of [x,y,z])
        [0,0,0], [1,0,0], [1,1,0], [0,1,0],
        [0,0,1], [1,0,1], [1,1,1], [0,1,1]
      ],
      "blocks": [                                       // REQUIRED
        {
          "hex": [0,1,2,3,4,5,6,7],                    // 8 vertex indices
          "cells": [20,20,1],                          // cell counts in x,y,z
          "grading_type": "simpleGrading",             // "simpleGrading" | "edgeGrading"
          "grading": [1,1,1]                           // or lists for edgeGrading
        }
      ],
      "patches": [                                      // REQUIRED
        {"name":"inlet","type":"patch","faces":[[0,4,7,3]]},
        {"name":"outlet","type":"patch","faces":[[1,2,6,5]]}
      ]
    }

    LLM_CALL_CONVENTION
    -------------------
    • Before invoking, the agent MUST echo: case_path, convertToMeters, vertex count,
      block count (with grading types), patch names; then ask for explicit confirmation.

    RETURNS (str, JSON)
    -------------------
      Success: {"status":"success","report":"..."}
      Error:   {"status":"error","error_message":"..."}
    """
    try:
        data = json.loads(config_json)

        case_path = data.get("case_path")
        vertices = data.get("vertices")
        blocks = data.get("blocks")
        patches = data.get("patches")
        convert_to_meters = data.get("convertToMeters", 1.0)

        if not case_path or vertices is None or blocks is None or patches is None:
            return json.dumps({
                "status": "error",
                "error_message": "Missing required fields: case_path, vertices, blocks, patches"
            }, ensure_ascii=False)

        system_dir = Path(case_path) / "system"
        if not system_dir.is_dir():
            return json.dumps({
                "status": "error",
                "error_message": f"System directory not found at '{system_dir}'."
            }, ensure_ascii=False)

        # Build sections
        vertices_str = _format_vertices(vertices)
        blocks_str = _format_blocks(blocks)
        boundary_str = _format_boundary(patches)

        content = f"""/*--------------------------------*- C++ -*----------------------------------*\\
| =========                 |                                                 |
| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |
|  \\    /   O peration     | Website:  https://openfoam.org                  |
|   \\  /    A nd           | Version:  7                                     |
|    \\/     M anipulation  |                                                 |
\\*---------------------------------------------------------------------------*/
FoamFile
{{
    version     2.0;
    format      ascii;
    class       dictionary;
    object      blockMeshDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

convertToMeters {convert_to_meters};

vertices
{vertices_str}

blocks
{blocks_str}

edges
(
);

boundary
{boundary_str}

// ************************************************************************* //
"""
        out_path = system_dir / "blockMeshDict"
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(content)

        return json.dumps({
            "status": "success",
            "report": f"Successfully wrote blockMeshDict to '{out_path}'."
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_message": f"An unexpected error occurred: {e}"
        }, ensure_ascii=False)


if __name__ == "__main__":
    # Smoke test
    TEST_CASE = "blockMeshDict_test_case"
    os.makedirs(os.path.join(TEST_CASE, "system"), exist_ok=True)
    os.makedirs(os.path.join(TEST_CASE, "constant"), exist_ok=True)

    config = {
        "case_path": TEST_CASE,
        "convertToMeters": 0.1,
        "vertices": [
            [0,0,0],[1,0,0],[1,1,0],[0,1,0],
            [0,0,1],[1,0,1],[1,1,1],[0,1,1]
        ],
        "blocks": [
            {"hex":[0,1,2,3,4,5,6,7],"cells":[20,20,1],"grading_type":"simpleGrading","grading":[1,5,1]}
        ],
        "patches": [
            {"name":"inlet","type":"patch","faces":[[0,4,7,3]]},
            {"name":"outlet","type":"patch","faces":[[1,2,6,5]]},
            {"name":"fixedWalls","type":"wall","faces":[[0,1,5,4],[2,3,7,6]]},
            {"name":"frontAndBack","type":"empty","faces":[[0,3,2,1],[4,5,6,7]]}
        ]
    }

    res = edit_blockMeshDict(json.dumps(config, ensure_ascii=False))
    print("RESULT:", res)

    # Show a snippet of the written file if success
    result = json.loads(res)
    if result.get("status") == "success":
        out_path = Path(TEST_CASE) / "system" / "blockMeshDict"
        with open(out_path, "r", encoding="utf-8") as f:
            print("\n--- blockMeshDict (first 80 lines) ---")
            for i, line in enumerate(f):
                print(line.rstrip())
                if i > 80:
                    break

    # Cleanup
    import shutil
    shutil.rmtree(TEST_CASE, ignore_errors=True)
    print(f"Cleaned up '{TEST_CASE}'.")
