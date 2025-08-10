import os
import sys
import json
import shutil
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from deepflame_interface.configuration_handler import CaseConfiguration

def add_region_config(case_name: str, region: dict) -> dict:
    """
    Adds a region configuration to the specified run case in task_manager.json.

    Args:
        case_name: The name of the run case (e.g. "2D_HIT_1").
        region: A dict describing the region to add, for example:
            {
                "type": "circle",
                "center": [0.025, 0.025, 0],
                "radius": 0.01,
            }

    Returns:
        A dictionary indicating the outcome:
            - On success:
                {
                    "status": "success",
                    "message": f"Added region to {case_name}.",
                    "regions": [...]  # the updated list of regions
                }
            - On error:
                {
                    "status": "error",
                    "error_message": "Description of the error."
                }
    """
    try:
        # df_agent_root = os.getenv('DF_AGENT_ROOT')
        # if df_agent_root is None:
        #     raise EnvironmentError("DF_AGENT_ROOT environment variable is not set.")

        df_agent_root = '/home/xu/test-6/deepflame-agent-dev/df_agent/agent'

        task_manager_path = Path(df_agent_root) / 'output' / 'task_manager.json'
        if not task_manager_path.is_file():
            raise FileNotFoundError(f"Task manager file not found at {task_manager_path}")

        # Load the existing task_manager.json
        with open(task_manager_path, 'r') as f:
            task_manager = json.load(f)

        run_cases = task_manager.get("run_cases", {})
        if case_name not in run_cases:
            return {
                "status": "error",
                "error_message": f"Run case '{case_name}' does not exist in task_manager.json."
            }

        case_config = run_cases[case_name].get("case_config", {})
        setfields = case_config.get("setFieldsDict", {})
        regions = setfields.get("regions", [])

        # Append the new region
        regions.append(region)

        # Write back the updated structure
        setfields["regions"] = regions
        case_config["setFieldsDict"] = setfields
        run_cases[case_name]["case_config"] = case_config
        task_manager["run_cases"] = run_cases

        with open(task_manager_path, 'w') as f:
            json.dump(task_manager, f, indent=2)

        return {
            "status": "success",
            "message": f"Added region to {case_name}.",
            "regions": regions
        }

    except (EnvironmentError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: {e}")
        return {"status": "error", "error_message": str(e)}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
    

def conduct_add_region(
    target_case_path: str,  
    region: str,        # 当前区域类型
    p1: str,
    p2: str,
    radius: float
) -> dict:
    
    p1 = " ".join(f"{x:.8f}" for x in p1)
    p2 = " ".join(f"{x:.8f}" for x in p2)
    # 共用的 fieldValues 字符串
    fv = """fieldValues
        (
            volScalarFieldValue T    2562.9164474426
            volScalarFieldValue H      0.0001388161
            volScalarFieldValue H2     0.0017201967
            volScalarFieldValue O      0.0007829835
            volScalarFieldValue OH     0.0088649505
            volScalarFieldValue H2O    0.2335677169
            volScalarFieldValue O2     0.0097972807
            volScalarFieldValue HO2    0.0000040007
            volScalarFieldValue H2O2   0.0000004494
            volScalarFieldValue N2     0.7451236055
        );"""

    if region == 'circle':
        new_block = f"""
    cylinderToCell
    {{
        p1 ({p1});
        p2 ({p2});
        radius {radius};
        {fv}
    }}"""

    elif region == 'square':
        new_block = f"""
    boxToCell
    {{
        boxes
        (
            ({p1})({p2})
        );
        {fv}
    }}"""

    elif region == 'ring':  # ring
        outer = 2 * float(radius)
        new_block = f"""
    cylinderAnnulusToCell
    {{
        p1 ({p1});
        p2 ({p2});
        innerRadius {radius};
        outerRadius {outer};
        {fv}
    }}"""

   
    set_fields_path = os.path.join(target_case_path, "system", "setFieldsDict")
    
    with open(set_fields_path, 'r') as f:
        lines = f.readlines()
    
    new_lines = []
    inserted = False
    for i, line in enumerate(lines):
        new_lines.append(line)
   
        if inserted:

            new_lines.append("\n")
            new_lines.append("\n")
                
            new_lines.append(new_block)
            inserted = False

        if "regions" in line:
            inserted = True
            
    
    # 4. 写回修改后的文件
    with open(set_fields_path, 'w') as f:
        f.writelines(new_lines)
    
    return {
        "status": "success",
        "inserted_block": new_block,
        "set_fields_path": set_fields_path
    }


def add_target_case_region(target_case_name: str) -> dict:
    # 1. 读取主配置文件 config.json
    cfg_path = Path("/home/xu/test-6/deepflame-agent-dev/df_agent/agent/output/task_manager.json")
    if not cfg_path.is_file():
        print(f"Error: {cfg_path} not found.")
        exit(1)

    with open(cfg_path, 'r') as f:
        cfg = json.load(f)

    run_cases = cfg.get("run_cases", {})
    print(run_cases)
    if target_case_name not in run_cases:
        print(f"Error: run case '{target_case_name}' not in config.json")
        exit(1)

    # 3. 从配置中读取 regions 列表
    regions = run_cases[target_case_name]["case_config"]["setFieldsDict"]["regions"]

    # 4. 定位目标算例路径下的 system/setFields 文件
    df_agent_root = '/home/xu/test-6/deepflame-agent-dev/df_agent/agent'
    task_path = Path(df_agent_root) / 'output' / 'df_runs' 

    target_case_path = os.path.join(task_path, target_case_name)

    # 5. 对每个 region 调用 conduct_add_region，收集新 block
    for idx, reg in enumerate(regions, start=1):
        region_type = reg.get("type")
        p1 = reg.get("p1")
        p2 = reg.get("p2")
        radius = reg.get("radius")
        res = conduct_add_region(target_case_path, region_type, p1, p2, radius)
        if res.get("status") != "success":
            print(f"Error generating block for region #{idx}: {res.get('error_message')}")
            exit(1)

    print(f"Successfully appended {idx} region blocks to setfieldsDict")






def add_regions_interactive(setFields_type: list, case_name: str) -> dict:
    """Interactively adds normalized region types to an existing list.

    This tool prompts the user to input a case name and a region description. Based on keywords about cases
    in the input, it normalizes one of: "2D_HIT_1" or "2D_HIT_2" or "2D_HIT_3". 
    Based on keywords about shapes in the input, it appends one of: "circle", "square", or "ring" for any times.
    If the normalized region already exists in setFields_type, an error is returned.
    Unsupported descriptions also yield an error.

    Normalization rules:
        - Input containing "圆"            -> normalized to "circle"
        - Input containing "方"            -> normalized to "square"
        - Input containing "环"            -> normalized to "ring"

    Attention:  
        the setFields_type shouldn't be [] or NULL

    Args:
        setFields_type: A list of strings representing the regions already added.
        for example and default: setFields_type = ['circle','square','ring']

    Returns:
        dict: Outcome of the operation:
            - Success:
                {
                  'status': 'success',
                  'message': 'Region added successfully.',
                  'regions': updated_list
                }
            - Unsupported region description:
                {
                  'status': 'error',
                  'error_message': 'Unsupported region type: "{raw_input}".'
                }
            - Duplicate region:
                {
                  'status': 'error',
                  'error_message': 'Region type "{normalized}" already added. '
                                   'Call update_regions_interactive instead.'
                }
            - Invalid (empty) input:
                {
                  'status': 'error',
                  'error_message': 'Invalid region description provided.'
                }

    Example success response:
        {
          'status': 'success',
          'message': 'Region added successfully.',
          'regions': ['circle', 'square']
        }

    Example error response:
        {
          'status': 'error',
          'error_message': 'Unsupported region type: "三角形".'
        }
    """

    if not setFields_type:
        return {
            'status': 'error',
            'error_message': 'setFields_type is empty. No regions to add.'
        }

    print(setFields_type)

    try:
        df_agent_root = '/home/xu/test-6/deepflame-agent-dev/df_agent/agent'
        task_path = Path(df_agent_root) / 'output' / 'df_runs'
        if not task_path.is_dir():
            raise FileNotFoundError(f"Directory not found: {task_path}")

        fi = case_name

        for idx in range(len(setFields_type)):
            region_type = setFields_type[idx]
            
            # 3. Build test_region dict
            if len(setFields_type) == 2 and idx == 0:
                test_region = {
                    "type": region_type,
                    "p1": [0.016755160, 0.025132741, 0],
                    "p2": [0.016755160, 0.025132741, 0.050265482],
                    "radius": 0.00102604,
                }
            if len(setFields_type) == 2 and idx == 1:
                test_region = {
                    "type": region_type,
                    "p1": [0.033510322, 0.025132741, 0],
                    "p2": [0.033510322, 0.025132741, 0.050265482],
                    "radius": 0.00102604,
                }
            if len(setFields_type) == 3 and idx == 0:
                test_region = {
                    "type": region_type,
                    "p1": [0.015455160, 0.018995942, 0],
                    "p2": [0.018055160, 0.021595942, 0.050265482],
                    "radius": 0.00102604,
                }
            if len(setFields_type) == 3 and idx == 1:
                test_region = {
                    "type": region_type,
                    "p1": [0.023832741, 0.033506338, 0],
                    "p2": [0.026432741, 0.036106338, 0.050265482],
                    "radius": 0.00102604,
                }
            if len(setFields_type) == 3 and idx == 2:
                test_region = {
                    "type": region_type,
                    "p1": [0.032210322, 0.018995942, 0],
                    "p2": [0.034810322, 0.021595942, 0.050265482],
                    "radius": 0.00102604,
                }
            if len(setFields_type) == 4 and idx == 0:
                test_region = {
                    "type": region_type,
                    "p1": [0.016755160, 0.016755160, 0],
                    "p2": [0.016755160, 0.016755160, 0.050265482],
                    "radius": 0.001256637,
                }
            if len(setFields_type) == 4 and idx == 1:
                test_region = {
                    "type": region_type,
                    "p1": [0.016755160, 0.033510322, 0],
                    "p2": [0.016755160, 0.033510322, 0.050265482],
                    "radius": 0.001256637,
                }
            if len(setFields_type) == 4 and idx == 2:
                test_region = {
                    "type": region_type,
                    "p1": [0.033510322, 0.016755160, 0],
                    "p2": [0.033510322, 0.016755160, 0.050265482],
                    "radius": 0.001256637,
                }
            if len(setFields_type) == 4 and idx == 3:
                test_region = {
                    "type": region_type,
                    "p1": [0.033510322, 0.033510322, 0],
                    "p2": [0.033510322, 0.033510322, 0.050265482],
                    "radius": 0.001256637,
                }


            # 4. Add to task_manager.json
            add_res = add_region_config(fi, test_region)


        add_target_case_region(fi)

        return {
            "status": "success",
            "setFields_type":setFields_type,
            "case_name":case_name
        }

    except Exception as e:
        return {
            "status": "error",
            "setFields_type":setFields_type,
            "case_name":case_name,
            "error_message": str(e)
        }





if __name__ == "__main__":
    setFields_type = ['circle','square','ring']
    add_regions_interactive(setFields_type)




















# def add_regions_interactive() -> dict:
#     """
#     Interactively adds a test region to every run case under df_agent_root/output/df_runs,
#     asking the user what initial field (“初场”) is needed for each case, and determining
#     the region shape based on keywords in the user’s answer.

#     For each case folder:
#       1. Prompt: “算例 <case_name> 的初场设置是 ......”
#       2. Read the user’s response (description).
#       3. Determine region type:
#          - contains "圆" -> type = "circle"
#          - contains "方" -> type = "square"
#          - contains "环" -> type = "ring"
#          - otherwise   -> type = "circle" (default)
#       4. Construct:
#          {
#            "type": <determined_type>,
#            "p1": [0.016755160, 0.016755160, 0],
#            "p2": [0.016755160, 0.016755160, 0.050265482],
#            "radius": 0.01
#          }
#       5. Call add_region_config(case_name, test_region)
#       6. Call add_target_case_region(case_name)
#       7. Collect per-case results.

#     Returns:
#         A dict indicating the outcome:
#         - On success:
#             {
#               "status": "success",
#               "results": {
#                 "<case1>": { ... result of add_region_config ... },
#                 "<case2>": { ... },
#                 ...
#               }
#             }
#         - On error:
#             {
#               "status": "error",
#               "error_message": "Description of the error."
#             }
#     """
#     try:
#         df_agent_root = '/home/xu/test-6/deepflame-agent-dev/df_agent/agent'
#         task_path = Path(df_agent_root) / 'output' / 'df_runs'
#         if not task_path.is_dir():
#             raise FileNotFoundError(f"Directory not found: {task_path}")

#         filenames = [p.name for p in task_path.iterdir() if p.is_dir()]
#         results = {}

#         for fi in filenames:
#             # 1. Prompt the user for this case's initial field description
#             prompt = f"算例 {fi} 的初场设置是 ...... "
#             desc = input(prompt).strip()

#             # 2. Determine region type from description
#             if "圆" in desc:
#                 region_type = "circle"
#             elif "方" in desc:
#                 region_type = "square"
#             elif "环" in desc:
#                 region_type = "ring"
#             else:
#                 region_type = "circle"

#             # 3. Build test_region dict
#             test_region = {
#                 "type": region_type,
#                 "p1": [0.016755160, 0.016755160, 0],
#                 "p2": [0.016755160, 0.016755160, 0.050265482],
#                 "radius": 0.01,
#             }

#             # 4. Add to task_manager.json
#             add_res = add_region_config(fi, test_region)
#             print(json.dumps(add_res, ensure_ascii=False, indent=2))
#             results[fi] = add_res

#             # 5. Further per-case setup
#             try:
#                 add_target_case_region(fi)
#             except Exception as e:
#                 results[fi]['add_target_case_region_error'] = str(e)

#         return {
#             "status": "success",
#             "results": results
#         }

#     except Exception as e:
#         return {
#             "status": "error",
#             "error_message": str(e)
#         }


# if __name__ == "__main__":
#     summary = add_regions_interactive()
#     print(json.dumps(summary, ensure_ascii=False, indent=2))











# if __name__ == "__main__":
#     df_agent_root = '/home/xu/test-6/deepflame-agent-dev/df_agent/agent'
#     task_path = Path(df_agent_root) / 'output' / 'df_runs' 
#     filenames = [p.name for p in task_path.iterdir()]

#     for fi in filenames:
#         test_region = {
#             "type": "circle",
#             "p1": [0.016755160, 0.016755160, 0],
#             "p2": [0.016755160, 0.016755160, 0.050265482],
#             "radius": 0.01,
#         }


#         result = add_region_config(fi, test_region)
#         print(json.dumps(result, indent=2))
#         add_target_case_region(fi)
        