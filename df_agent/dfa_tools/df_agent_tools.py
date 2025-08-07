import os
import sys
import subprocess

import matplotlib.pyplot as plt

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from deepflame_interface.df_agent_utils import read_openfoam_scalar

def check_bashrc_loaded() -> dict:
    """Checks if the DeepFlame and OpenFOAM bashrc files are loaded in the current environment.

    Use this tool to verify the loading of necessary environment configurations.
    This is important for ensuring that DeepFlame and OpenFOAM are set up correctly.

    Returns:
        A dictionary indicating the result of the check.
        Possible statuses: 'success', 'error', 'not_loaded'.
        Example success: {'status': 'success', 'message': 'Both DeepFlame and OpenFOAM bashrc are loaded.'}
        Example error: {'status': 'error', 'error_message': 'Environment variables not found.'}
        Example not_loaded: {'status': 'not_loaded', 'missing': ['DeepFlame', 'OpenFOAM']}
    """
    deepflame_loaded = 'DF_ROOT' in os.environ
    openfoam_loaded = 'WM_PROJECT_DIR' in os.environ

    missing = []
    if not deepflame_loaded:
        missing.append('DeepFlame')
    if not openfoam_loaded:
        missing.append('OpenFOAM')

    if not missing:
        # Retrieve the values of the environment variables
        deepflame_path = os.environ['DF_ROOT']
        openfoam_path = os.environ['WM_PROJECT_DIR']
        
        return {
            "status": "success",
            "message": (f"Both DeepFlame and OpenFOAM bashrc are loaded.\n"
                        f"DeepFlame path: {deepflame_path}\n"
                        f"OpenFOAM path: {openfoam_path}")
        }
    else:
        return {
            "status": "not_loaded",
            "missing": missing
        }

def run_allrun_script(case_path: str) -> dict:
    """Executes the Allrun script located in the specified case path.

    Use this tool ONLY when a user requests to run the Allrun script for 
    a specific case. Ensure that the case path provided is valid and accessible.

    Args:
        case_path: The file path to the directory containing the Allrun script.

    Returns:
        A dictionary indicating the result of the execution.
        Possible statuses: 'success', 'error'.
        Example success: {'status': 'success', 'message': 'Allrun script executed successfully.'}
        Example error: {'status': 'error', 'error_message': 'Script not found in the specified path.'}
    """
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
        return {
            "status": "success",
            "message": "Allrun script executed successfully.",
            "output": result.stdout
        }
    except subprocess.CalledProcessError as e:
        return {
            "status": "error",
            "error_message": f"Error executing Allrun script: {e.stderr}"
        }
        
def read_and_save_openfoam_scalars(directory: str, output_file: str) -> dict:
    """Reads OpenFOAM scalar files 'T' and 'Cx' from the specified directory and writes their data to a new text file.

    Use this tool ONLY when you need to read scalar files from a specified directory and save the results
    in a text file. This is important for processing simulation data from OpenFOAM.

    Args:
        directory: The path to the directory containing the 'T' and 'Cx' scalar files.
        output_file: The path to the output text file where the data will be saved.

    Returns:
        A dictionary indicating the result of the operation.
        Possible statuses: 'success', 'error', 'file_not_found'.
        Example success: {'status': 'success', 'message': 'Data successfully written to output.txt.'}
        Example error: {'status': 'error', 'error_message': 'Failed to read scalar files.'}
        Example file_not_found: {'status': 'file_not_found', 'missing_files': ['T', 'Cx']}
    """
    scalar_files = ['T', 'Cx']
    all_data = {}
    missing_files = []

    for scalar in scalar_files:
        file_path = os.path.join(directory, scalar)
        if os.path.isfile(file_path):
            all_data[scalar] = read_openfoam_scalar(file_path)
        else:
            missing_files.append(scalar)

    if missing_files:
        return {
            "status": "file_not_found",
            "missing_files": missing_files
        }

    try:
        with open(output_file, 'w') as out_file:
            # Write the header
            out_file.write("T, Cx\n")
            
            # Find the maximum length to handle unequal arrays
            max_length = max(len(all_data['T']), len(all_data['Cx']))

            for i in range(max_length):
                # Get the T and Cx values, defaulting to an empty string if out of bounds
                t_value = all_data['T'][i] if i < len(all_data['T']) else ''
                cx_value = all_data['Cx'][i] if i < len(all_data['Cx']) else ''
                
                out_file.write(f"{t_value}, {cx_value}\n")

        return {
            "status": "success",
            "message": f"Data successfully written to {output_file}."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }
        
        
def plot_openfoam_data(input_file: str) -> dict:
    """Plots the data from the specified text file containing 'T' and 'Cx' values.

    Use this tool ONLY when you need to visualize the simulation data from OpenFOAM
    saved in the specified text file. This is important for analyzing trends in the data.

    Args:
        input_file: The path to the text file containing 'T' and 'Cx' data.

    Returns:
        A dictionary indicating the result of the operation.
        Possible statuses: 'success', 'error', 'file_not_found'.
        Example success: {'status': 'success', 'message': 'Plot generated successfully.'}
        Example error: {'status': 'error', 'error_message': 'Failed to read data.'}
        Example file_not_found: {'status': 'file_not_found', 'error_message': 'Input file does not exist.'}
    """
    try:
        # Check if the input file exists
        if not os.path.isfile(input_file):
            return {
                "status": "file_not_found",
                "error_message": "Input file does not exist."
            }

        # Read the data from the file
        data = []
        with open(input_file, 'r') as f:
            # Skip the header
            next(f)
            for line in f:
                values = line.strip().split(',')
                if len(values) == 2:
                    data.append((float(values[0]), float(values[1])))

        # Unzip the data into T and Cx
        T, Cx = zip(*data)

        # Create the plot
        plt.figure(figsize=(10, 5))
        plt.plot(Cx, T, marker='o', linestyle='-', color='b', label='Cx vs T')
        plt.title('Cx vs T Plot')
        plt.ylabel('Temperature (T)')
        plt.xlabel('Location')
        plt.grid()
        plt.legend()
        plt.tight_layout()

        # Show the plot
        plt.show()

        return {
            "status": "success",
            "message": "Plot generated successfully."
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e)
        }