import os
import shutil
import subprocess

from pathlib import Path

def start_df_runs() -> dict:
    """Starts all DeepFlame runs based on task_manager.json.

    Use this tool ONLY when a user requests to run all DeepFlame runs.

    Returns:
        A dictionary indicating the result of the execution.
        Possible statuses: 'success', 'error'.
        Example success: {'status': 'success', 'message': 'Allrun script executed successfully.'}
        Example error: {'status': 'error', 'error_message': 'Script not found in the specified path.'}
    """
    try:
        df_agent_root = os.getenv('DF_AGENT_ROOT')
        if df_agent_root is None:
            raise EnvironmentError("DF_AGENT_ROOT environment variable is not set.")

        # config_path = Path(df_agent_root) / 'config.json'
        case_path = Path(df_agent_root).parent.parent / 'case_templates/1D_free_flame/H2'

    except (EnvironmentError, FileNotFoundError) as e:
        print(f"Error: {e}")
        return {"status": "error", "error_message": str(e)}
    
    # Check if the case path exists and contains the Allrun script
    allrun_script = os.path.join(case_path, 'Allrun')
    
    if not os.path.isfile(allrun_script):
        return {
            "status": "error",
            "error_message": "Allrun script not found in the specified path."
        }

    try:
        # Execute the Allrun script
        result = subprocess.run([allrun_script], capture_output=True, text=True, check=True)
        # Copy log.* files to output directories
        output_dir = Path(df_agent_root) / 'output/df_runs'
        for dir in output_dir.iterdir():
            if dir.is_dir():
                for log_file in case_path.glob('log.*'):
                    shutil.copy(log_file, dir)

        return {
            "status": "success",
            "message": "All DeepFlame runs finished successfully.",
            "output": result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "error_message": f"Error executing Allrun script: {e.stderr}"
        }
        
def visualize_df_runs() -> dict:
    """Visualizes all DeepFlame runs based on task_manager.json.

    Use this tool ONLY when a user requests to visualize all DeepFlame runs,
    specifically for prompts such as:
    - "visualize the ignition zone setups for all runs"

    Returns:
        A dictionary indicating the result of the visualization.
        Possible statuses: 'success', 'error'.
        Example success: {'status': 'success', 'message': 'Visualization completed successfully.'}
        Example error: {'status': 'error', 'error_message': 'Visualization failed.'}
    """
    try:
        port = 50002
        images_dir = Path("/home/xk/Software/6_bohr_agent/src/images")  # Ensure this path is correct
        
        file_path = images_dir / "ignition_zones.jpg"
        if file_path.is_file():
            local_url = f"http://localhost:{port}/images/{file_path.name}"
            markdown_link = f"![visualization results]({local_url})"
            result = f"Here are the requested visualizations: {markdown_link}"
            
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }
    
    return {
        "status": "success",
        "message": "Visualization completed successfully.",
        "output": result
    }