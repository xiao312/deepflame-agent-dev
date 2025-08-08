import json
import os
from pathlib import Path


def setup_case_directory(config_json: str) -> str:
    """
    Create a standard OpenFOAM case directory structure.

    PARAMETERS (single JSON string; MUST confirm with user before calling)
    ---------------------------------------------------------------------
    config_json example:
    {
      "case_name": "H2_flame_test",             // REQUIRED; folder name only
      "base_dir": ".",                          // OPTIONAL (default: ".")
      "layout": ["0", "constant", "system"],    // OPTIONAL (default as shown)
      "overwrite": false                          // OPTIONAL; if true and exists, ensure subdirs exist
    }

    LLM_CALL_CONVENTION
    -------------------
    • Before invoking, the agent MUST echo: full path (base_dir/case_name),
      layout (subfolders), and overwrite flag; then ask for explicit user
      confirmation ("确认/confirm").

    RETURNS (str, JSON)
    -------------------
      Success: {"status":"success","report":"...","path":"<abs path>","created":[...]} 
      Error:   {"status":"error","error_message":"..."}
    """
    try:
        data = json.loads(config_json)

        case_name = data.get("case_name")
        base_dir = data.get("base_dir", ".")
        layout = data.get("layout", ["0", "constant", "system"])
        overwrite = bool(data.get("overwrite", False))

        # Basic validation for the case name to avoid invalid characters
        if not case_name or any(c in r'/\\?%*:|"<>"' for c in case_name):
            return json.dumps({
                "status": "error",
                "error_message": f"Invalid case name '{case_name}'. Please avoid special characters."
            }, ensure_ascii=False)

        case_path = Path(base_dir) / case_name
        abs_path = case_path.resolve()

        if case_path.exists() and not overwrite:
            return json.dumps({
                "status": "error",
                "error_message": f"Directory '{abs_path}' already exists. Set overwrite=true to reuse it."
            }, ensure_ascii=False)

        # Create main dir and subdirectories
        case_path.mkdir(parents=True, exist_ok=True)
        created = []
        for sub in layout:
            sub_path = case_path / sub
            if not sub_path.exists():
                sub_path.mkdir(parents=True, exist_ok=True)
                created.append(str(sub_path))

        return json.dumps({
            "status": "success",
            "report": f"Case directory ready at '{abs_path}'.",
            "path": str(abs_path),
            "created": created
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_message": f"An unexpected error occurred: {e}"
        }, ensure_ascii=False)


if __name__ == "__main__":
    # Smoke test
    TEST_BASE = "."
    TEST_NAME = "my_first_case"

    # 1) Fresh create
    cfg1 = {"case_name": TEST_NAME, "base_dir": TEST_BASE}
    print("CREATE:", setup_case_directory(json.dumps(cfg1, ensure_ascii=False)))

    # 2) Try create again without overwrite (should error)
    cfg2 = {"case_name": TEST_NAME, "base_dir": TEST_BASE}
    print("RE-CREATE (no overwrite):", setup_case_directory(json.dumps(cfg2, ensure_ascii=False)))

    # 3) Reuse with overwrite and custom layout
    cfg3 = {"case_name": TEST_NAME, "base_dir": TEST_BASE, "overwrite": True, "layout": ["0","constant","system","postProcessing"]}
    print("REUSE (overwrite):", setup_case_directory(json.dumps(cfg3, ensure_ascii=False)))

    # Cleanup
    import shutil
    shutil.rmtree(Path(TEST_BASE) / TEST_NAME, ignore_errors=True)
    print(f"Cleaned up '{TEST_NAME}'.")
