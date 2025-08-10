import io
import os
import sys
import json
import shutil
import warnings
import contextlib
from pathlib import Path

from .xde_utils import xde_inference, xde_visualize

def xde_inference_tool() -> dict:
    """Executes inference using the XDEBench models on the prepared dataset.

    Use this tool ONLY when you need to perform inference on a dataset that has 
    already been prepared in a specified location. After completion, the tool 
    analyzes the inference results to identify the best-performing model based 
    on metrics such as accuracy, precision, or recall.

    Returns:
        A dictionary containing the result of the inference process.
        Possible statuses include:
        - 'success': Inference completed without issues, including performance metrics.
        - 'error': An error occurred during the process.

        Example success:
        {
            'status': 'success',
            'message': 'Inference completed successfully.',
            'output': 'Inference results including performance metrics...'
        }

        Example error:
        {
            'status': 'error',
            'error_message': 'Inference process failed due to an internal error.'
        }

    After running this tool, review the 'output' for detailed performance 
    metrics of each model. Use this information to select the best-performing 
    model according to your specific criteria (e.g., highest accuracy).
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


def xde_visualize_tool() -> dict:
    """Executes visualization of the XDEBench models' results.

    This tool visualizes the results of the inference performed on the dataset.
    It generates visualizations based on the inference results and saves them 
    in the specified output directory. If the visualizations are successfully 
    created, it copies the resulting files to a static images directory and 
    constructs Markdown links for easy display.

    Returns:
        A dictionary containing the result of the visualization process.
        Possible statuses include:
        - 'success': Visualization completed without issues, including file copying 
          and Markdown link generation.
        - 'error': An error occurred during the process, with a message detailing 
          the issue.
        
        Example success:
        {'status': 'success', 'message': 'Visualization completed successfully. Here are the results:\n![可选的替代文字](http://localhost:50002/images/model.gif)'}
        
        Example error:
        {'status': 'error', 'error_message': 'Visualization failed due to missing config file.'}
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
    
    model_names = [
        'CNextv2-seed-0-7_31_3_24_19_52157',
        'FactFormerv2-seed-0-7_29_15_0_21_64290',
        'FFNO-seed-0-7_31_0_4_7_94912',
    ]
    expected_files = [output_path / f"{model_name}/temperature_series.gif" for model_name in model_names]
    
    try:
        xde_visualize()
        
        # Prepare to collect results
        results = []
        port = 50002
        images_dir = Path("/home/xk/Software/6_bohr_agent/src/images")  # Ensure this path is correct
        images_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist

        # Check for existing files and construct URLs
        for model_name, file_path in zip(model_names, expected_files):
            if file_path.is_file():
                try:
                    # Copy the image to the static images directory
                    filename = model_name.split('-')[0] + ".gif"
                    destination_path = images_dir / filename
                    shutil.copy(file_path, destination_path)  # Copy the file

                    # Construct the URL for the local web server
                    local_url = f"http://localhost:{port}/images/{filename}"

                    # Prepare the Markdown link for display
                    markdown_link = f"![visualization results]({local_url})"
                    results.append(f"Here are the visualization results for {model_name}:\n{markdown_link}")
                except Exception as e:
                    results.append(f"Error loading image for {model_name}: {str(e)}")

        # Combine results into a final message
        final_message = "\n\n".join(results)
        return {"status": "success", "message": final_message}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}


def query_available_models() -> dict:
    """Introduces currently available operator learning models for PDE tasks.

    Use this tool when a user queries about available operator learning models.
    It provides a brief overview of three representative frameworks, each with unique advantages
    in different PDE modeling tasks.

    Returns:
        A dictionary containing the details of the available models.
        Possible statuses include:
        - 'success': Information retrieved successfully.
        - 'error': An error occurred during the process.

        Example success:
        {
            'status': 'success',
            'models': [
                {
                    'name': 'FFNO',
                    'description': 'Factorized Fourier Neural Operators, which effectively captures long-range dependencies while reducing parameter count and computational cost.',
                    'reference': 'Factorized Fourier Neural Operators.'
                },
                {
                    'name': 'FactFormer',
                    'description': 'Scalable Transformer for PDE Surrogate Modeling, optimized for spatial-temporal encoding and sparse attention mechanisms.',
                    'reference': 'Scalable Transformer for PDE Surrogate Modeling.'
                },
                {
                    'name': 'CNext',
                    'description': 'A ConvNet for the 2020s, enhancing the classic U-Net with modern convolution designs for improved stability and generalization.',
                    'reference': 'A ConvNet for the 2020s.'
                }
            ]
        }

        Example error:
        {'status': 'error', 'error_message': 'Unable to retrieve model information.'}
    """
    try:
        models_info = [
            {
                'name': 'FFNO',
                'description': (
                    'Factorized Fourier Neural Operators, which effectively captures long-range dependencies while reducing parameter count and computational cost.'
                ),
                'reference': 'Factorized Fourier Neural Operators.'
            },
            {
                'name': 'FactFormer',
                'description': (
                    'Scalable Transformer for PDE Surrogate Modeling, optimized for spatial-temporal encoding and sparse attention mechanisms.'
                ),
                'reference': 'Scalable Transformer for PDE Surrogate Modeling.'
            },
            {
                'name': 'CNext',
                'description': (
                    'A ConvNet for the 2020s, enhancing the classic U-Net with modern convolution designs for improved stability and generalization.'
                ),
                'reference': 'A ConvNet for the 2020s.'
            }
        ]
        
        return {
            'status': 'success',
            'models': models_info
        }
    except Exception as e:
        return {
            'status': 'error',
            'error_message': str(e)
        }