import json
import os
from pathlib import Path


def edit_controlDict(config_json: str) -> str:
    """
    Create or overwrite `system/controlDict` with specified run controls.

    PARAMETERS (single JSON string; MUST confirm with user before calling)
    ---------------------------------------------------------------------
    config_json example:
    {
      "case_path": "output/2D_HIT_template",  // REQUIRED
      "application": "icoFoam",                // REQUIRED
      "startTime": 0.0,                         // REQUIRED
      "endTime": 10.0,                          // REQUIRED
      "deltaT": 0.005,                          // REQUIRED
      "writeInterval": 1,                       // REQUIRED

      // Optional (defaults are applied inside the function)
      "startFrom": "startTime",                // startTime | latestTime
      "stopAt": "endTime",                     // endTime | writeNow | nextWrite
      "writeControl": "adjustableRunTime",     // timeStep | runTime | adjustableRunTime
      "purgeWrite": 0,
      "writeFormat": "ascii",                   // ascii | binary
      "writeCompression": false,                // true | false
      "timeFormat": "general",                 // general | fixed | scientific
      "timePrecision": 6,
      "runTimeModifiable": true,

      // Optional adaptive time step controls
      "maxCo": 0.9,                             // if provided -> adjustTimeStep yes
      "maxDeltaT": 1.0
    }

    LLM_CALL_CONVENTION
    -------------------
    • Before invoking, the agent MUST echo: case_path, application, time window
      (startTime→endTime), deltaT, writeControl/writeInterval, and whether adaptive
      time stepping (maxCo/maxDeltaT) is enabled; then ask for explicit confirmation.

    RETURNS (str, JSON)
    -------------------
      Success: {"status":"success","report":"Successfully wrote controlDict to '...'."}
      Error:   {"status":"error","error_message":"..."}
    """
    try:
        data = json.loads(config_json)

        # --- Required fields ---
        case_path = data.get("case_path")
        application = data.get("application")
        startTime = data.get("startTime")
        endTime = data.get("endTime")
        deltaT = data.get("deltaT")
        writeInterval = data.get("writeInterval")

        if (not case_path or not application or startTime is None or endTime is None or
                deltaT is None or writeInterval is None):
            return json.dumps({
                "status": "error",
                "error_message": (
                    "Missing required fields: case_path, application, startTime, "
                    "endTime, deltaT, writeInterval"
                )
            }, ensure_ascii=False)

        # --- Optional fields with internal defaults ---
        startFrom = data.get("startFrom", "startTime")
        stopAt = data.get("stopAt", "endTime")
        writeControl = data.get("writeControl", "adjustableRunTime")
        purgeWrite = int(data.get("purgeWrite", 0))
        writeFormat = data.get("writeFormat", "ascii")
        writeCompression = bool(data.get("writeCompression", False))
        timeFormat = data.get("timeFormat", "general")
        timePrecision = int(data.get("timePrecision", 6))
        runTimeModifiable = bool(data.get("runTimeModifiable", True))
        maxCo = data.get("maxCo")
        maxDeltaT = data.get("maxDeltaT")

        # Paths & existence
        system_dir = Path(case_path) / "system"
        if not system_dir.is_dir():
            return json.dumps({
                "status": "error",
                "error_message": f"System directory not found at '{system_dir}'."
            }, ensure_ascii=False)

        control_dict_path = system_dir / "controlDict"

        # Optional adaptive timestep block
        if maxCo is not None:
            adjust_time_step = "yes"
            courant_block = (
                f"adjustTimeStep  {adjust_time_step};\n"
                f"maxCo           {maxCo};\n"
                f"maxDeltaT       { (maxDeltaT if maxDeltaT is not None else 1) };\n"
            )
        else:
            courant_block = ""

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
    format      {writeFormat};
    class       dictionary;
    location    "system";
    object      controlDict;
}}
// * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * * //

application     {application};

startFrom       {startFrom};

startTime       {startTime};

stopAt          {stopAt};

endTime         {endTime};

deltaT          {deltaT};

writeControl    {writeControl};

writeInterval   {writeInterval};

purgeWrite      {purgeWrite};

writeFormat     {writeFormat};

writeCompression { 'on' if writeCompression else 'off' };

timeFormat      {timeFormat};

timePrecision   {timePrecision};

runTimeModifiable { 'true' if runTimeModifiable else 'false' };
{courant_block}// ************************************************************************* //
"""

        with open(control_dict_path, "w", encoding="utf-8") as f:
            f.write(content)

        return json.dumps({
            "status": "success",
            "report": f"Successfully wrote controlDict to '{control_dict_path}'."
        }, ensure_ascii=False)

    except Exception as e:
        return json.dumps({
            "status": "error",
            "error_message": f"An unexpected error occurred: {e}"
        }, ensure_ascii=False)


if __name__ == "__main__":
    # Smoke test for edit_controlDict
    TEST_CASE = "controlDict_test_case"
    os.makedirs(os.path.join(TEST_CASE, "system"), exist_ok=True)

    # Test 1: Basic controlDict
    cfg1 = {
        "case_path": TEST_CASE,
        "application": "icoFoam",
        "startTime": 0,
        "endTime": 10,
        "deltaT": 0.005,
        "writeInterval": 1
    }
    res1 = edit_controlDict(json.dumps(cfg1, ensure_ascii=False))
    print("RESULT 1:", res1)

    # Test 2: With adaptive timestep controls
    cfg2 = {
        "case_path": TEST_CASE,
        "application": "pimpleFoam",
        "startTime": 0,
        "endTime": 100,
        "deltaT": 1e-5,
        "writeInterval": 10,
        "maxCo": 0.9,
        "maxDeltaT": 1.0
    }
    res2 = edit_controlDict(json.dumps(cfg2, ensure_ascii=False))
    print("RESULT 2:", res2)

    # Show file content snippet
    path = Path(TEST_CASE) / "system" / "controlDict"
    if path.exists():
        print("\n--- controlDict content ---")
        with open(path, "r", encoding="utf-8") as f:
            print(f.read())

    # Cleanup
    import shutil
    shutil.rmtree(TEST_CASE, ignore_errors=True)
    print(f"Cleaned up '{TEST_CASE}'.")
