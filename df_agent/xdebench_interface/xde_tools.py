import io
import os
import sys
import json
import warnings
import contextlib
from pathlib import Path
from .xde_utils import xde_inference

def xde_inference_tool(data_path: str) -> dict:
    """Performs inference using the XDEBench models on the specified data path.

    Use this tool when you want to evaluate models in the XDEBench framework
    with a given dataset. Ensure the data path points to the correct location of
    the data files.

    Args:
        data_path: The absolute path to the directory containing the data for inference.

    Returns:
        A dictionary containing the result of the inference process.
        Possible statuses: 'success', 'error'.
        Example success: {'status': 'success', 'message': 'Inference completed successfully.'}
        Example error: {'status': 'error', 'error_message': 'Data path not found or invalid.'}
    """
    try:
        df_agent_root = os.getenv('DF_AGENT_ROOT')
        if df_agent_root is None:
            raise EnvironmentError("DF_AGENT_ROOT environment variable is not set.")
        output_path = Path(df_agent_root) / 'output' / 'xde_runs'
        output_path.mkdir(parents=True, exist_ok=True)

        config_path = Path(df_agent_root) / 'config.json'
        if not config_path.is_file():
            raise FileNotFoundError(f"Config file not found at {config_path}")

        with open(config_path) as config_file:
            config_data = json.load(config_file)
        xde_src = config_data.get('xdebench', {}).get('src')
        xde_data = config_data.get('xdebench', {}).get('data')
        
        sys.path.insert(0, xde_src)

    except (EnvironmentError, FileNotFoundError, json.JSONDecodeError) as e:
        return {"status": "error", "error_message": str(e)}
    
    output_message = io.StringIO()  # Create a string buffer to capture output
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")  # Suppress warnings
            with contextlib.redirect_stdout(output_message):  # Redirect stdout to the buffer
                xde_inference()

        # Capture the output
        output = output_message.getvalue()
        output = output.replace(xde_src, "$XDE_SRC").replace(xde_data, "$XDE_DATA")

        return {
            "status": "success",
            "message": "Inference completed successfully.",
            "output": output.strip()  # Pass the captured output
        }
    except Exception as e:
        return {"status": "error", "error_message": str(e)}