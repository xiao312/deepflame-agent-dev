import json
from pathlib import Path


def _format_foam_dict_recursive(data: dict, indent_level: int = 1) -> str:
    """
    Recursively format a Python dictionary into an OpenFOAM-style dictionary body.
    Generic helper; safe for reuse by other tools.
    """
    lines = []
    indent = "    " * indent_level
    for key, value in data.items():
        if isinstance(value, dict):
            lines.append(f"{indent}{key}")
            lines.append(f"{indent}{{")
            lines.append(_format_foam_dict_recursive(value, indent_level + 1))
            lines.append(f"{indent}}}")
        elif isinstance(value, list):
            list_str = " ".join(map(str, value))
            lines.append(f"{indent}{key.ljust(25)}{list_str};")
        else:
            lines.append(f"{indent}{key.ljust(25)}{value};")
    return "\n".join(lines)


def edit_physical_properties(config_json: str) -> str:
    """
    Create or overwrite multiple properties files in the `constant/` directory.

    PARAMETERS (single JSON to avoid ADK schema issues)
    --------------------------------------------------
    config_json (str, JSON):
      {
        "case_path": "C:/path/to/H2_flame_test",   // REQUIRED; absolute or relative
        "properties": {                             // REQUIRED; map filename -> dict content
          "transportProperties": {
            "transportModel": "Newtonian",
            "nu": "[0 2 -1 0 0 0 0] 1.48e-05"
          },
          "turbulenceProperties": {
            "simulationType": "laminar"
          },
          "combustionProperties": {
            "combustion": "off"
          }
        }
      }

    LLM_CALL_CONVENTION (VERY IMPORTANT)
    ------------------------------------
    • Before invoking this tool, the agent MUST show the user a preview of:
      - case_path
      - file list to be written (keys of `properties`)
      - for each file, a short snippet (first lines) of the generated content
      and ask for explicit confirmation (e.g., "确认/confirm").
    • Proceed ONLY after user confirmation.

    RETURNS (str, JSON)
    -------------------
      Success:
        {"status": "success", "report": "Successfully wrote properties files: [...]"}
      Error (missing dirs / bad input / exceptions):
        {"status": "error", "error_message": "..."}
    """
    try:
        data = json.loads(config_json)

        # --- Required inputs ---
        if "case_path" not in data:
            return json.dumps({
                "status": "error",
                "error_message": "Missing required field: case_path"
            }, ensure_ascii=False)
        if "properties" not in data:
            return json.dumps({
                "status": "error",
                "error_message": "Missing required field: properties (object)"
            }, ensure_ascii=False)

        case_path = data["case_path"]
        properties = data["properties"]
        if not isinstance(properties, dict) or not properties:
            return json.dumps({
                "status": "error",
                "error_message": "'properties' must be a non-empty object mapping filename -> dict"
            }, ensure_ascii=False)

        case_dir = Path(case_path)
        constant_dir = case_dir / "constant"
        if not constant_dir.is_dir():
            return json.dumps({
                "status": "error",
                "error_message": f"Constant directory not found at '{constant_dir}'."
            }, ensure_ascii=False)

        written = []
        for file_name, content_dict in properties.items():
            if not isinstance(content_dict, dict):
                return json.dumps({
                    "status": "error",
                    "error_message": f"Value for '{file_name}' must be an object (dict)."
                }, ensure_ascii=False)

            file_path = constant_dir / file_name

            header = [
                "/*--------------------------------*- C++ -*----------------------------------*\\",
                "| =========                 |                                                 |",
                "| \\\\      /  F ield         | OpenFOAM: The Open Source CFD Toolbox           |",
                "|  \\\\    /   O peration     | Website:  https://openfoam.org                  |",
                "|   \\\\  /    A nd           | Version:  7                                     |",
                "|    \\\\/     M anipulation  |                                                 |",
                "\\*---------------------------------------------------------------------------*/",
                "FoamFile",
                "{",
                "    version     2.0;",
                "    format      ascii;",
                "    class       dictionary;",
                f"    object      {file_name};",
                "}",
                "// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //",
                "",
            ]

            body = _format_foam_dict_recursive(content_dict, 0)
            footer = "\n// ************************************************************************* //"
            content = "\n".join(header + [body, footer])

            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)
            written.append(file_name)

        return json.dumps({
            "status": "success",
            "report": f"Successfully wrote properties files: {written}."
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_message": f"An unexpected error occurred: {e}"
        }, ensure_ascii=False)


if __name__ == "__main__":
    sample = {
        "case_path": "./properties_test_case",
        "properties": {
            "transportProperties": {
                "transportModel": "Newtonian",
                "nu": "[0 2 -1 0 0 0 0] 1.48e-05"
            },
            "turbulenceProperties": {
                "simulationType": "laminar"
            },
            "combustionProperties": {
                "combustion": "off"
            }
        }
    }

    # ✅ 必须先创建 constant 目录
    Path(sample["case_path"], "constant").mkdir(parents=True, exist_ok=True)

    print(edit_physical_properties(json.dumps(sample, ensure_ascii=False)))

