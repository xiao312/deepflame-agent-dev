import os
import sys
import json
import shutil

import numpy as np
import imageio.v2 as imageio
import matplotlib.pyplot as plt

from pathlib import Path

def xde_inference():
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
        print(f"Error: {e}")
        return

    
    from evaluator.utils import extract_best_results, evaluate_model
    
    experiment_name = "hit"  # Change as needed

    extract_best_results(
        data_path=xde_data, 
        experiment_name=experiment_name, evalutor="test_error"
    )
    evaluate_model(
        data_path=xde_data, 
        experiment_name=experiment_name, device='cpu', seed=0
    )
    
    # Check for best_results.csv and bestModelsEvaluator.csv
    for filename in ['best_results.csv', 'bestModelsEvaluator.csv']:
        src_file = Path(xde_data) / filename
        if src_file.is_file():
            shutil.move(str(src_file), str(output_path / filename))
            
    # Check for bestModelResults directory
    best_model_results_dir = Path(xde_data) / 'bestModelResults'
    if best_model_results_dir.is_dir():
        for subdir in best_model_results_dir.iterdir():
            if subdir.is_dir():
                events_files = sorted(subdir.glob("events.*"))
                if events_files:
                    # Move the first sorted events file to output_path
                    first_event_file = events_files[0]
                    relative_path = subdir.relative_to(best_model_results_dir)
                    target_dir = output_path / relative_path

                    # Create target directory if it doesn't exist
                    target_dir.mkdir(parents=True, exist_ok=True)

                    # Move the file
                    shutil.move(str(first_event_file), str(target_dir / first_event_file.name))

def xde_visualize():
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
        print(f"Error: {e}")
        return
    
    model_names = [
        'CNextv2-seed-0-7_31_3_24_19_52157',
        'FactFormerv2-seed-0-7_29_15_0_21_64290',
        'FFNO-seed-0-7_31_0_4_7_94912',
    ]
    hit_idxs = [
        1, 2, 0
    ]
    hit_titles = [
        '2D_HIT_1',
        '2D_HIT_2',
        '2D_HIT_3',
    ]

    cvode_npz_path = Path(xde_data) / 'data/hit.npz'
    cvode_npz = np.load(cvode_npz_path)
    cvode_data = cvode_npz['test_data']
    print(cvode_data.shape)

    # model_idx = 0
    for model_idx in range(len(model_names)):
        model_data_path = Path(xde_data) / f'bestModelResults/{model_names[model_idx]}/states.npy'
        model_data = np.load(model_data_path)
        print(model_data.shape)

        # Create output directory for images
        output_dir = output_path / f'{model_names[model_idx]}' / 'slices'
        os.makedirs(output_dir, exist_ok=True)

        # List to store filenames for GIF creation
        filenames = []

        # Set font sizes
        row_title_size = 24  # Largest for row titles
        subplot_title_size = 16  # Second largest for subplot titles
        label_size = 14  # Smaller for labels

        # Loop through the second dimension (30 slices)
        for time_idx in range(cvode_data.shape[1]):
            plot_data = [
                cvode_data[hit_idxs[0], time_idx, -2, :, :],
                cvode_data[hit_idxs[1], time_idx, -2, :, :],
                cvode_data[hit_idxs[2], time_idx, -2, :, :],
                model_data[hit_idxs[0], time_idx, -4, :, :],
                model_data[hit_idxs[1], time_idx, -4, :, :],
                model_data[hit_idxs[2], time_idx, -4, :, :],
            ]

            # Determine global min and max for color scaling
            global_min = 500
            global_max = 2700

            # Create a figure with subplots
            fig, axes = plt.subplots(2, 3, figsize=(15, 10))

            # Loop to create 6 snapshots
            for i, ax in enumerate(axes.flatten()):
                slice_data = plot_data[i]
                # print(slice_data.shape)
                
                # Create normalized grid
                x = np.linspace(0, 1, slice_data.shape[1])
                y = np.linspace(0, 1, slice_data.shape[0])
                X, Y = np.meshgrid(x, y)

                # Plot the contour using the normalized grid
                contour = ax.contourf(
                    X, Y, slice_data, 
                    levels=np.linspace(global_min, global_max, 23), 
                    cmap='viridis', 
                    vmin=global_min, vmax=global_max,
                )
                
                # Set title and labels
                ax.set_title(
                    hit_titles[i % 3], 
                    fontsize=subplot_title_size, 
                    pad=10,
                )
                
                # Set x and y limits to normalized coordinates
                ax.set_xlim(0, 1)  # Normalize x-axis
                ax.set_ylim(0, 1)  # Normalize y-axis

                # Set aspect ratio to 1
                ax.set_aspect('equal', adjustable='box')
                
                # Only label ticks for left column and bottom row
                ax.set_xticks([0, 0.25, 0.5, 0.75, 1])
                ax.set_xlabel(r'$x/x_{max}$', fontsize=label_size)
                if i % 3 == 0:  # Left column
                    ax.set_yticks([0, 0.25, 0.5, 0.75, 1])  # Y ticks
                    ax.set_ylabel(r'$y/y_{max}$', fontsize=label_size)
                else:
                    ax.set_yticks([])  # Remove Y ticks for other columns

            # Create a shared colorbar
            cbar = fig.colorbar(
                contour, ax=axes.ravel().tolist(), 
                orientation='vertical', 
                label='Temperature [K]', 
                shrink=0.9, 
                aspect=25
            )
            cbar.ax.set_ylabel('Temperature [K]', fontsize=20, labelpad=20)

            # Add shared titles for the rows
            cntr = 0.437
            fig.text(
                cntr, 0.9, 
                'Groud Truth', 
                ha='center', va='center', 
                fontsize=row_title_size,
                fontweight='bold',
            )
            fig.text(
                cntr, 0.48, 
                'Model Prediction', 
                ha='center', va='center', 
                fontsize=row_title_size,
                fontweight='bold',
            )

            # Save the plot as a JPEG file
            filename = f"{output_dir}/slice_{time_idx}.jpg"
            plt.savefig(filename)
            plt.close()
            
            # Append filename for GIF
            filenames.append(filename)

        # Create a GIF from the saved images
        gif_filename = output_path / f'{model_names[model_idx]}' / 'temperature_series.gif'
        images = [imageio.imread(filename) for filename in filenames]

        # Add the last frame again for a pause effect
        pause_frame = images[-1]  # Get the last image
        images.append(pause_frame)  # Add it again for pause

        # Save the GIF with a small pause
        imageio.mimsave(gif_filename, images, duration=1, loop=0)  # Loop=0 for infinite loop

        print(f"GIF saved as {gif_filename}")
        
        shutil.rmtree(output_dir)


if __name__ == "__main__":
    os.environ['DF_AGENT_ROOT'] = '/home/xk/Software/6_bohr_agent/deepflame-agent-dev/df_agent/agent'
    # xde_inference()
    xde_visualize()