import json
from pathlib import Path


def check_case_completeness(config_json: str) -> str:
    """
    Check whether an OpenFOAM case directory is "complete" in a basic sense.

    Parameters (single JSON string to avoid ADK schema issues):
    -----------------------------------------------------------
    config_json (str, JSON):
      {
        "case_path": "C:/path/to/H2_flame_test",            // REQUIRED
        "required_fields": ["U", "p", "T", "H2", "O2"]  // REQUIRED (list of field files expected under 0/)
      }

    LLM_CALL_CONVENTION (VERY IMPORTANT):
    ------------------------------------
    • Before invoking this tool, the agent MUST parse the JSON and SHOW the user the
      following parameters for confirmation: case_path, required_fields.
    • Proceed ONLY after the user explicitly confirms (e.g., "yes" / "confirm").

    Returns (str, JSON):
    --------------------
      On success (all files present):
        {"status": "success", "report": "Case '...' is complete. All required files are present."}

      On error (missing files or other issues):
        {
          "status": "error",
          "error_message": "...",
          "missing_files": ["system/controlDict", "0/U", ...]
        }

    Notes:
    ------
    • This is a lightweight structural check. Real-world completeness may require
      solver-specific files beyond the basics listed here.
    """
    try:
        data = json.loads(config_json)

        # --- Required inputs ---
        if "case_path" not in data:
            return json.dumps({
                "status": "error",
                "error_message": "Missing required field: case_path",
                "missing_files": []
            }, ensure_ascii=False)
        if "required_fields" not in data:
            return json.dumps({
                "status": "error",
                "error_message": "Missing required field: required_fields (list)",
                "missing_files": []
            }, ensure_ascii=False)

        case_path = data["case_path"]
        required_fields = data["required_fields"]

        # Basic validation
        if not isinstance(required_fields, list):
            return json.dumps({
                "status": "error",
                "error_message": "'required_fields' must be a list of field names.",
                "missing_files": []
            }, ensure_ascii=False)

        case_dir = Path(case_path)

        # 1) Main case directory exists?
        if not case_dir.is_dir():
            return json.dumps({
                "status": "error",
                "error_message": f"Case directory '{case_path}' not found.",
                "missing_files": [case_path]
            }, ensure_ascii=False)

        # 2) Essential file list (minimal baseline)
        essential_files = [
            "system/controlDict",
            "system/fvSchemes",
            "system/fvSolution",
            # Presence of boundary often means blockMesh has run and polyMesh exists
            "constant/polyMesh/boundary",
        ]

        # Add required 0/ field files
        for field in required_fields:
            essential_files.append(f"0/{field}")

        # 3) Scan for missing
        missing_files = []
        for rel in essential_files:
            abs_path = case_dir / rel
            abs_path_gz = abs_path.with_suffix(abs_path.suffix + '.gz') if abs_path.suffix else abs_path.with_name(abs_path.name + '.gz')

            if not abs_path.exists() and not abs_path_gz.exists():
                # Neither uncompressed nor compressed file exists
                missing_files.append(rel + "(.gz)")

        # 4) Build result
        if not missing_files:
            return json.dumps({
                "status": "success",
                "report": f"Case '{case_path}' is complete. All required files are present."
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "status": "error",
                "error_message": f"Case '{case_path}' is incomplete. The following files are missing:",
                "missing_files": missing_files
            }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_message": f"An unexpected error occurred: {e}",
            "missing_files": []
        }, ensure_ascii=False)


if __name__ == "__main__":
    # Minimal smoke test (no defaults in signature; runtime-only examples are fine)
    example = {
        "case_path": ".\cases\oneD_freelyPropagation\H2",
        "required_fields": ["U", "p", "T", "O2", "N2"]
    }
    print(check_case_completeness(json.dumps(example, ensure_ascii=False)))
