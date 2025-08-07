import os
import sys
import json
import shutil
from pathlib import Path

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from deepflame_interface.configuration_handler import CaseConfiguration

def initialize_task_manager(case_type: str, case_num: int) -> dict:
    """Initializes the task manager for specified run cases based on user input.

    This tool should be used when the user provides a description that includes 
    specific case types such as "HIT", "二维HIT", "hit", or "2D_HIT". The function
    will automatically normalize the case type to "2D_HIT" if any of these keywords 
    are detected in the input. If the input case type does not match any supported 
    types, an error will be returned.

    Args:
        case_type: A string indicating the type of case to be initialized. 
                   Valid values include "2D_HIT", "HIT", "二维HIT", or variations 
                   like "hit" and "2d_HIT". If any of these are provided, 
                   they will be normalized to "2D_HIT".
        case_num: An integer representing the number of instances to create 
                  for the specified case type. This should be a positive integer.

    Returns:
        A dictionary indicating the outcome of the operation:
            - If successful: {'status': 'success', 'message': 'Task manager initialized successfully.'}
            - If unsupported case type: {'status': 'error', 'error_message': 'Unsupported case type: {case_type}'}
            - If invalid case number: {'status': 'error', 'error_message': 'Invalid case number provided.'}
            - If task manager already exists: {'status': 'error', 'error_message': 'Task manager already exists. Call update_task_manager instead.'}
    
    Example success response:
        {'status': 'success', 'message': 'Task manager initialized successfully.'}

    Example error response:
        {'status': 'error', 'error_message': 'Unsupported case type: "unknown_case_type".'}
    """
    try:
        df_agent_root = os.getenv('DF_AGENT_ROOT')
        if df_agent_root is None:
            raise EnvironmentError("DF_AGENT_ROOT environment variable is not set.")

        config_path = Path(df_agent_root) / 'config.json'
        if not config_path.is_file():
            raise FileNotFoundError(f"Config file not found at {config_path}")

        with open(config_path) as config_file:
            config_data = json.load(config_file)
        SUPPORTED_CASE_TYPES = config_data.get('SUPPORTED_CASE_TYPES')

        task_manager_path = Path(df_agent_root) / 'output' / 'task_manager.json'

    except (EnvironmentError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: {e}")
        return {"status": "error", "error_message": str(e)}

    if task_manager_path.exists():
        return {"status": "error", "error_message": "Task manager already exists. Call update_task_manager instead."}

    try:
        if case_type not in SUPPORTED_CASE_TYPES:
            return {"status": "error", "error_message": f"Unsupported case type: {case_type}"}
        
        if case_num <= 0:
            return {"status": "error", "error_message": "Invalid case number provided."}

        run_cases = {}
        for case_index in range(1, case_num + 1):
            case_name = f"{case_type}_{case_index}"
            run_cases[case_name] = {
                "case_type": case_type,
                "case_config": CaseConfiguration(case_type).to_dict()  # Placeholder for CaseConfiguration
            }

        # Save to task_manager.json
        with open(task_manager_path, 'w') as f:
            json.dump({"run_cases": run_cases}, f, indent=2)

        return {"status": "success", "message": "Task manager initialized successfully."}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


async def initialize_tasks() -> dict:
    """Initializes tasks based on the information in output/task_manager.json.

    This tool should be called immediately after initialize_task_manager
    has succeeded. It creates necessary output directories and copies 
    template directories for each registered run case.

    Returns:
        A dictionary indicating the outcome of the operation:
            - If successful: {'status': 'success', 'message': 'Tasks initialized successfully.'}
            - If task manager does not exist: {'status': 'error', 'error_message': 'Task manager does not exist.'}
    """
    try:
        df_agent_root = os.getenv('DF_AGENT_ROOT')
        if df_agent_root is None:
            raise EnvironmentError("DF_AGENT_ROOT environment variable is not set.")

        config_path = Path(df_agent_root) / 'config.json'
        if not config_path.is_file():
            raise FileNotFoundError(f"Config file not found at {config_path}")

        with open(config_path) as config_file:
            config_data = json.load(config_file)
        SUPPORTED_CASE_TYPES = config_data.get('SUPPORTED_CASE_TYPES')

        task_manager_path = Path(df_agent_root) / 'output' / 'task_manager.json'

    except (EnvironmentError, FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error: {e}")
        return {"status": "error", "error_message": str(e)}

    if not task_manager_path.exists():
        return {"status": "error", "error_message": "Task manager does not exist."}

    try:
        with open(task_manager_path, 'r') as f:
            task_manager = json.load(f)

        # Create output directories
        df_runs_dir = Path("output/df_runs")
        xde_runs_dir = Path("output/xde_runs")
        df_runs_dir.mkdir(parents=True, exist_ok=True)
        xde_runs_dir.mkdir(parents=True, exist_ok=True)

        # Copy template directories for each run case
        for run_case in task_manager["run_cases"]:
            case_type = run_case["case_type"]
            case_name = run_case["name"]

            # Assuming you have a template directory structure
            template_dir = Path(f"templates/{case_type}")  # Adjust the path as necessary
            target_dir = df_runs_dir / case_name
            shutil.copytree(template_dir, target_dir)

        return {"status": "success", "message": "Tasks initialized successfully."}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}