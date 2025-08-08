import json
from pathlib import Path
from typing import Any


def _format_dimensions(dims: list) -> str:
    """Formats a list of 7 integers into an OpenFOAM dimensions string."""
    return f"[{ ' '.join(map(str, dims)) }]"


def _format_value(value: Any) -> str:
    """Formats a Python value into an OpenFOAM-compatible string."""
    if isinstance(value, str) and not value.startswith('('):
        return f'"{value}"'  # quote plain strings such as zeroGradient, uniform 101325
    if isinstance(value, (list, tuple)):
        return f"({' '.join(map(str, value))})"  # vectors/tuples
    return str(value)


def _format_boundary_field(conditions: dict) -> str:
    """Formats the boundaryField dictionary body."""
    lines = ["    {"]
    for patch_name, patch_data in conditions.items():
        lines.append(f"        {patch_name}")
        lines.append("        {")
        for key, value in patch_data.items():
            lines.append(f"            {key.ljust(20)}{_format_value(value)};")
        lines.append("        }")
    lines.append("    }")
    return "\n".join(lines)


def _format_internal_field(field_data: dict) -> str:
    """Formats the internalField entry."""
    field_type = field_data.get("type", "uniform")

    if field_type == "uniform":
        value_str = _format_value(field_data.get("value", 0))
        return f"internalField   uniform {value_str};"

    if field_type == "nonuniform":
        values = field_data.get("values", [])
        value_type = "scalar"
        if values and isinstance(values[0], (list, tuple)):
            value_type = "vector"
        lines = [f"internalField   nonuniform List<{value_type}>"]
        lines.append(str(len(values)))
        lines.append("(")
        for val in values:
            lines.append(_format_value(val))
        lines.append(")")
        lines.append(";")
        return "\n".join(lines)

    return f"// Unsupported internal field type: {field_type}"



def create_initial_field_from_template(config_json: str) -> str:
    """
    Create an initial field file under the `0/` directory from a JSON template.

    PARAMETERS (single JSON string; MUST confirm with user before calling)
    ---------------------------------------------------------------------
    config_json example:
    {
      "case_path": "C:/path/to/H2_flame_test",                // REQUIRED
      "field_name": "T",                                      // REQUIRED
      "field_class": "volScalarField",                        // OPTIONAL (default: volScalarField)
      "dimensions": [0, 0, 0, 1, 0, 0, 0],                     // REQUIRED (7 ints)
      "internal_field": {                                      // REQUIRED
        "type": "uniform",                                    // "uniform" | "nonuniform"
        "value": 300                                           // if uniform
        // or
        // "type": "nonuniform",
        // "values": [300, 301, 302, ...]                      // if nonuniform
      },
      "boundary_conditions": {                                 // REQUIRED
        "inlet":  {"type": "fixedValue",   "value": 300},
        "outlet": {"type": "zeroGradient"},
        "walls":  {"type": "zeroGradient"}
      }
    }

    LLM_CALL_CONVENTION
    -------------------
    • Before invoking, the agent MUST echo back to the user for confirmation:
      case_path, field_name, field_class, a summary of dimensions/internal_field,
      and a preview of boundary patch names.
    • Proceed ONLY after explicit confirmation (e.g., "确认/confirm").

    RETURNS (str, JSON)
    -------------------
      Success:
        {"status": "success", "report": "Successfully created initial field file for 'T'."}
      Error:
        {"status": "error", "error_message": "..."}
    """
    try:
        data = json.loads(config_json)

        # --- Required fields ---
        case_path = data.get("case_path")
        field_name = data.get("field_name")
        dimensions = data.get("dimensions")
        internal_field = data.get("internal_field")
        boundary_conditions = data.get("boundary_conditions")
        field_class = data.get("field_class", "volScalarField")

        # Basic validation
        if not case_path or not field_name or dimensions is None or internal_field is None or boundary_conditions is None:
            return json.dumps({
                "status": "error",
                "error_message": "Missing required fields: case_path, field_name, dimensions, internal_field, boundary_conditions"
            }, ensure_ascii=False)

        if not isinstance(dimensions, list) or len(dimensions) != 7:
            return json.dumps({
                "status": "error",
                "error_message": "'dimensions' must be a list of 7 numbers"
            }, ensure_ascii=False)

        if not isinstance(boundary_conditions, dict) or not boundary_conditions:
            return json.dumps({
                "status": "error",
                "error_message": "'boundary_conditions' must be a non-empty object"
            }, ensure_ascii=False)

        # Prepare paths
        zero_dir = Path(case_path) / "0"
        if not zero_dir.is_dir():
            return json.dumps({
                "status": "error",
                "error_message": f"Zero directory not found at '{zero_dir}'."
            }, ensure_ascii=False)

        # Render content
        dims_str = _format_dimensions(dimensions)
        internal_field_str = _format_internal_field(internal_field)
        boundary_field_str = _format_boundary_field(boundary_conditions)

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
    class       {field_class};
    object      {field_name};
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

dimensions      {dims_str};

{internal_field_str}

boundaryField
{boundary_field_str}

// ************************************************************************* //
"""

        file_path = zero_dir / field_name
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return json.dumps({
            "status": "success",
            "report": f"Successfully created initial field file for '{field_name}'."
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_message": f"An unexpected error occurred while creating field '{data.get('field_name', '<unknown>')}': {e}"
        }, ensure_ascii=False)


if __name__ == "__main__":

    import json
    import os
    from pathlib import Path
    # Temporary test directory
    TEST_CASE_NAME = "initial_field_test_case"
    zero_dir = Path(TEST_CASE_NAME) / "0"
    os.makedirs(zero_dir, exist_ok=True)

    # Example config for a uniform scalar field 'p'
    config = {
        "case_path": TEST_CASE_NAME,
        "field_name": "p",
        "field_class": "volScalarField",
        "dimensions": [0, 2, -2, 0, 0, 0, 0],
        "internal_field": {"type": "uniform", "value": 101325},
        "boundary_conditions": {
            "inlet": {"type": "zeroGradient"},
            "outlet": {"type": "fixedValue", "value": "uniform 101325"},
            "walls": {"type": "zeroGradient"}
        }
    }

    # Call the function
    result_json = create_initial_field_from_template(json.dumps(config, ensure_ascii=False))
    print("Result:", result_json)

    # Verify file content if successful
    result = json.loads(result_json)
    if result.get("status") == "success":
        field_file = zero_dir / config["field_name"]
        print(f"\n--- Content of '{field_file}' ---")
        with open(field_file, 'r', encoding='utf-8') as f:
            print(f.read())

    # Clean up
    import shutil
    shutil.rmtree(TEST_CASE_NAME)
    print(f"Cleaned up '{TEST_CASE_NAME}' directory.")
