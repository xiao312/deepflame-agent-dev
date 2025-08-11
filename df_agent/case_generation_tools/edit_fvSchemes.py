import json
import os
from pathlib import Path
from typing import Any


def _format_schemes_dict(schemes_data: dict) -> str:
    """Helper: format a dictionary of schemes into OpenFOAM dictionary body."""
    lines = []
    for key, value in schemes_data.items():
        lines.append(f"    {key.ljust(25)}{value};")
    return "\n".join(lines)


def edit_fvSchemes(config_json: str) -> str:
    """
    Create or overwrite `system/fvSchemes` with structured parameters.

    PARAMETERS (single JSON string; MUST confirm with user before calling)
    ---------------------------------------------------------------------
    config_json example:
    {
      "case_path": "output/2D_HIT_template",    // REQUIRED
      "schemes": {                        // REQUIRED
        "ddtSchemes": {"default": "Euler"},
        "gradSchemes": {"default": "Gauss linear"},
        "divSchemes": {
          "default": "none",
          "div(phi,U)": "Gauss linearUpwindV grad(U)",
          "div(phi,k)": "Gauss upwind",
          "div((nuEff*dev2(T(grad(U)))))": "Gauss linear"
        },
        "laplacianSchemes": {"default": "Gauss linear corrected"},
        "interpolationSchemes": {"default": "linear"},
        "snGradSchemes": {"default": "corrected"}
      }
    }

    LLM_CALL_CONVENTION
    -------------------
    • Before invoking, the agent MUST echo: case_path and a list of top-level
      scheme groups to be written (keys of `schemes`) and ask for explicit user
      confirmation ("确认/confirm").

    RETURNS (str, JSON)
    -------------------
      Success: {"status":"success","report":"Successfully wrote fvSchemes to '...'."}
      Error:   {"status":"error","error_message":"..."}
    """
    try:
        data = json.loads(config_json)

        case_path = data.get("case_path")
        schemes = data.get("schemes")
        if not case_path or not isinstance(schemes, dict) or not schemes:
            return json.dumps({
                "status": "error",
                "error_message": "Missing or invalid required fields: case_path, schemes(Object)"
            }, ensure_ascii=False)

        system_dir = Path(case_path) / "system"
        if not system_dir.is_dir():
            return json.dumps({
                "status": "error",
                "error_message": f"System directory not found at '{system_dir}'."
            }, ensure_ascii=False)

        fv_schemes_path = system_dir / "fvSchemes"

        # Build the file content dynamically
        header = [
            "/*--------------------------------*- C++ -*----------------------------------*\\",
            "| =========                 |                                                 |",
            "| \\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |",
            "|  \\    /   O peration     | Website:  https://openfoam.org                  |",
            "|   \\  /    A nd           | Version:  7                                     |",
            "|    \\/     M anipulation  |                                                 |",
            "\\*---------------------------------------------------------------------------*/",
            "FoamFile",
            "{",
            "    version     2.0;",
            "    format      ascii;",
            "    class       dictionary;",
            "    location    \"system\";",
            "    object      fvSchemes;",
            "}",
            "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //",
            ""
        ]

        body_lines = []
        for scheme_type, scheme_body in schemes.items():
            if not isinstance(scheme_body, dict):
                return json.dumps({
                    "status": "error",
                    "error_message": f"Scheme group '{scheme_type}' must be an object (dict)."
                }, ensure_ascii=False)
            body_lines.append(f"{scheme_type}")
            body_lines.append("{")
            body_lines.append(_format_schemes_dict(scheme_body))
            body_lines.append("}")
            body_lines.append("")

        footer = ["// ************************************************************************* //"]

        content = "\n".join(header + body_lines + footer)

        with open(fv_schemes_path, "w", encoding="utf-8") as f:
            f.write(content)

        return json.dumps({
            "status": "success",
            "report": f"Successfully wrote fvSchemes to '{fv_schemes_path}'."
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_message": f"An unexpected error occurred: {e}"
        }, ensure_ascii=False)


if __name__ == "__main__":
    # Smoke test
    TEST_CASE = "fvSchemes_test_case"
    os.makedirs(os.path.join(TEST_CASE, "system"), exist_ok=True)

    my_schemes = {
        "ddtSchemes": {"default": "Euler"},
        "gradSchemes": {"default": "Gauss linear"},
        "divSchemes": {
            "default": "none",
            "div(phi,U)": "Gauss linearUpwindV grad(U)",
            "div(phi,k)": "Gauss upwind",
            "div((nuEff*dev2(T(grad(U)))))": "Gauss linear"
        },
        "laplacianSchemes": {"default": "Gauss linear corrected"},
        "interpolationSchemes": {"default": "linear"},
        "snGradSchemes": {"default": "corrected"}
    }

    res = edit_fvSchemes(json.dumps({"case_path": TEST_CASE, "schemes": my_schemes}, ensure_ascii=False))
    print("RESULT:", res)

    # Show file content
    path = Path(TEST_CASE) / "system" / "fvSchemes"
    if path.exists():
        print("\n--- fvSchemes content ---")
        with open(path, "r", encoding="utf-8") as f:
            print(f.read())

    # Cleanup
    import shutil
    shutil.rmtree(TEST_CASE, ignore_errors=True)
    print(f"Cleaned up '{TEST_CASE}'.")
