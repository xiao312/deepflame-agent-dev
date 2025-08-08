import json
from pathlib import Path

# ---- Configuration ----
# Expect a single mechanism file placed next to this script:
#   Burke2012_s9r23.yaml
DB_FILE = Path(__file__).parent / "Burke2012_s9r23.yaml"
DB_KEY = "Burke2012_s9r23"  # the mechanism_name expected by the query

def _load_single_mech() -> dict:
    """
    Load the only mechanism from DB_FILE. Raise clear errors if missing.
    Returns a dict compatible with the old mock_db shape.
    """
    if not DB_FILE.exists():
        raise FileNotFoundError(f"Mechanism file not found: {DB_FILE}")
    content = DB_FILE.read_text(encoding="utf-8")
    return {
        DB_KEY: {
            "file_name": DB_FILE.name,
            "content": content,
        }
    }

def query_chemkinetics(config_json: str) -> str:
    """
    Query the single-file mock database for a chemical kinetics mechanism.

    Parameters (JSON string, must confirm with user before calling):
    {
      "mechanism_name": "Burke2012_s9r23",   // REQUIRED
      "species": ["H2", "O2", "N2"]           // REQUIRED (list of species)
    }

    Returns (JSON string):
      Success: {"status": "success", "report": "...", "file_name": "...", "content": "..."}
      Error:   {"status": "error", "error_message": "..."}
    """
    try:
        data = json.loads(config_json)
        mechanism_name = data.get("mechanism_name")
        species = data.get("species")

        if not mechanism_name or not isinstance(species, list):
            return json.dumps({"status": "error", "error_message": "Missing or invalid required fields: mechanism_name, species"}, ensure_ascii=False)

        mock_db = _load_single_mech()

        if mechanism_name in mock_db:
            mech = mock_db[mechanism_name]
            return json.dumps({
                "status": "success",
                "report": f"Successfully found mechanism '{mechanism_name}'.",
                "file_name": mech["file_name"],
                "content": mech["content"].strip()
            }, ensure_ascii=False)
        else:
            return json.dumps({
                "status": "error",
                "error_message": f"Mechanism '{mechanism_name}' not found. Available: {list(mock_db.keys())}"
            }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"status": "error", "error_message": f"Unexpected error: {e}"}, ensure_ascii=False)


def place_constant_file(config_json: str) -> str:
    """
    Write content to a specified file within the 'constant' directory.

    Parameters (JSON string, must confirm with user before calling):
    {
      "case_path": "C:/path/to/H2_flame_test",   // REQUIRED
      "file_name": "Burke2012_s9r23.yaml",       // REQUIRED
      "content": "<file contents>"               // REQUIRED
    }

    Returns (JSON string):
      Success: {"status": "success", "report": "..."}
      Error:   {"status": "error", "error_message": "..."}
    """
    try:
        data = json.loads(config_json)
        case_path = data.get("case_path")
        file_name = data.get("file_name")
        content = data.get("content")

        if not case_path or not file_name or not isinstance(content, str):
            return json.dumps({"status": "error", "error_message": "Missing or invalid required fields: case_path, file_name, content"}, ensure_ascii=False)

        # basic filename safety
        if any(sep in file_name for sep in ("..", "/", "\\")):
            return json.dumps({"status": "error", "error_message": f"Invalid file_name '{file_name}'."}, ensure_ascii=False)

        constant_dir = Path(case_path) / "constant"
        if not constant_dir.is_dir():
            return json.dumps({"status": "error", "error_message": f"Constant directory not found at '{constant_dir}'."}, ensure_ascii=False)

        file_path = constant_dir / file_name
        file_path.write_text(content, encoding="utf-8")

        return json.dumps({"status": "success", "report": f"Successfully placed file '{file_name}' in '{constant_dir}'."}, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"status": "error", "error_message": f"Unexpected error while placing file: {e}"}, ensure_ascii=False)


# --- smoke test: only runs if executed directly ---
if __name__ == "__main__":
    # 1) Query the mechanism (requires the YAML to be next to this script)
    cfg = {"mechanism_name": DB_KEY, "species": ["H2", "O2", "N2"]}
    print(query_chemkinetics(json.dumps(cfg, ensure_ascii=False)))

    # 2) Create a dummy case and write the mechanism into constant/
    case = "chem_test_case"
    (Path(case) / "constant").mkdir(parents=True, exist_ok=True)

    cfg2 = {
        "case_path": case,
        "file_name": "Burke2012_s9r23.yaml",
        "content": "description: test file\n"
    }
    print(place_constant_file(json.dumps(cfg2, ensure_ascii=False)))

    # 3) Verify write
    out = Path(case) / "constant" / cfg2["file_name"]
    print("exists:", out.exists())
    if out.exists():
        print(out.read_text(encoding="utf-8"))

    # 4) Cleanup (comment out if you want to inspect files)
    import shutil
    shutil.rmtree(case, ignore_errors=True)
