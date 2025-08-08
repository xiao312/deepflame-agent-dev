import os
import sys
import json
import shutil
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

if __name__ == "__main__":
    os.environ['DF_AGENT_ROOT'] = '/home/xk/Software/6_bohr_agent/deepflame-agent-dev/df_agent/agent'
    xde_inference()