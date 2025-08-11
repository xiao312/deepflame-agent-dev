import json
import os
from pathlib import Path
from typing import Any


def _format_dict_to_foam_entry(data: dict, indent_level: int = 1) -> str:
    """Recursively format a Python dictionary into an OpenFOAM dictionary body."""
    lines = []
    indent = "    " * indent_level
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent}{key}")
            lines.append(f"{indent}{{")
            lines.append(_format_dict_to_foam_entry(value, indent_level + 1))
            lines.append(f"{indent}}}")
        else:
            lines.append(f"{indent}{key.ljust(20)}{value};")
    return "\n".join(lines)


def edit_fvSolution(config_json: str) -> str:
    """
    Create or overwrite `system/fvSolution` with structured parameters.

    PARAMETERS (single JSON string; MUST confirm with user before calling)
    ---------------------------------------------------------------------
    config_json example:
    {
      "case_path": "output/2D_HIT_template",        // REQUIRED
      "solvers": {                            // REQUIRED (object)
        "\"(p|p_rgh)\"": {                  // keys can be raw names or regex strings quoted
          "solver": "PCG",
          "preconditioner": "DIC",
          "tolerance": 1e-6,
          "relTol": 0.1
        },
        "\"(U|k|epsilon)\"": {
          "solver": "PBiCGStab",
          "preconditioner": "DILU",
          "tolerance": 1e-8,
          "relTol": 0
        }
      },
      "algorithms": {                        // OPTIONAL (object), e.g. PIMPLE/PISO/SIMPLE
        "PIMPLE": {
          "nOuterCorrectors": 1,
          "nCorrectors": 2,
          "nNonOrthogonalCorrectors": 1,
          "pRefCell": 0,
          "pRefValue": 0,
          "residualControl": {"p": 1e-2, "U": 1e-3}
        }
      }
    }

    LLM_CALL_CONVENTION
    -------------------
    • Before invoking, the agent MUST echo: case_path, the list of solver entries
      (keys under `solvers`), and algorithm blocks to be written; then request
      explicit confirmation ("确认/confirm").

    RETURNS (str, JSON)
    -------------------
      Success: {"status":"success","report":"Successfully wrote fvSolution to '...'."}
      Error:   {"status":"error","error_message":"..."}
    """
    try:
        data = json.loads(config_json)

        case_path = data.get("case_path")
        solvers = data.get("solvers")
        algorithms = data.get("algorithms")

        if not case_path or not isinstance(solvers, dict) or not solvers:
            return json.dumps({
                "status": "error",
                "error_message": "Missing or invalid required fields: case_path, solvers(object)"
            }, ensure_ascii=False)

        system_dir = Path(case_path) / "system"
        if not system_dir.is_dir():
            return json.dumps({
                "status": "error",
                "error_message": f"System directory not found at '{system_dir}'."
            }, ensure_ascii=False)

        fv_solution_path = system_dir / "fvSolution"

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
            "    object      fvSolution;",
            "}",
            "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //",
            ""
        ]

        body = []
        body.append("solvers")
        body.append("{")
        body.append(_format_dict_to_foam_entry(solvers))
        body.append("}")
        body.append("")

        if algorithms:
            if not isinstance(algorithms, dict):
                return json.dumps({
                    "status": "error",
                    "error_message": "'algorithms' must be an object if provided"
                }, ensure_ascii=False)
            for algo_name, algo_params in algorithms.items():
                if not isinstance(algo_params, dict):
                    return json.dumps({
                        "status": "error",
                        "error_message": f"Algorithm block '{algo_name}' must be an object"
                    }, ensure_ascii=False)
                body.append(algo_name)
                body.append("{")
                body.append(_format_dict_to_foam_entry(algo_params))
                body.append("}")
                body.append("")

        footer = ["// ************************************************************************* //"]

        content = "\n".join(header + body + footer)

        with open(fv_solution_path, "w", encoding="utf-8") as f:
            f.write(content)

        return json.dumps({
            "status": "success",
            "report": f"Successfully wrote fvSolution to '{fv_solution_path}'."
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_message": f"An unexpected error occurred: {e}"
        }, ensure_ascii=False)


if __name__ == "__main__":
    # Smoke test
    TEST_CASE = "fvSolution_test_case"
    os.makedirs(os.path.join(TEST_CASE, "system"), exist_ok=True)

    my_solvers = {
        "\"(p|p_rgh)\"": {
            "solver": "PCG",
            "preconditioner": "DIC",
            "tolerance": 1e-06,
            "relTol": 0.1
        },
        "\"(U|k|epsilon)\"": {
            "solver": "PBiCGStab",
            "preconditioner": "DILU",
            "tolerance": 1e-08,
            "relTol": 0
        }
    }

    my_algorithms = {
        "PIMPLE": {
            "nOuterCorrectors": 1,
            "nCorrectors": 2,
            "nNonOrthogonalCorrectors": 1,
            "pRefCell": 0,
            "pRefValue": 0,
            "residualControl": {"p": 1e-2, "U": 1e-3}
        }
    }

    cfg = {"case_path": TEST_CASE, "solvers": my_solvers, "algorithms": my_algorithms}
    res = edit_fvSolution(json.dumps(cfg, ensure_ascii=False))
    print("RESULT:", res)

    # Show file content
    path = Path(TEST_CASE) / "system" / "fvSolution"
    if path.exists():
        print("\n--- fvSolution content ---")
        with open(path, "r", encoding="utf-8") as f:
            print(f.read())

    # Cleanup
    import shutil
    shutil.rmtree(TEST_CASE, ignore_errors=True)
    print(f"Cleaned up '{TEST_CASE}'.")
