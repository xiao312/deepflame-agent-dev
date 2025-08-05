import numpy as np

def read_openfoam_scalar(file_path):
    """Read scalar values from an OpenFOAM file."""
    with open(file_path, 'r') as file:
        lines = file.readlines()

    # Initialize variables
    internal_field_index = None
    uniform_value = None
    expected_count = None
    start_index = None
    end_index = None

    # Find the indices for the internal field values
    for i, line in enumerate(lines):
        if "internalField" in line:
            internal_field_index = i
            if ";" in line: # For uniform fields
                parts = line.split()
                # Assuming format: "internalField uniform <value>;"
                uniform_value = float(parts[-1][:-1])
                return uniform_value  # Return uniform as a 1x1 array
            else:
                # Read the next line for the expected count
                expected_count = int(lines[i + 1].strip())  # Convert to int
                # print(expected_count)
                # Check the next line for "("
                if "(" in lines[i + 2] and ")" in lines[i + 2 + expected_count + 1]:
                    start_index = i + 2  # Start reading values from the next line
                    end_index = i + 2 + expected_count + 1
                    
                    selected_lines = lines[start_index+1:end_index]
                    dim_array = np.loadtxt(selected_lines).reshape(-1, )
                    break  # Exit loop after processing

    return dim_array