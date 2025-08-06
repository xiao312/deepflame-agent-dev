import os
import sys

def xde_inference(data_path):
    target_dir = os.path.abspath('/home/xk/Software/6_bohr_agent/XDEBench/XDEBench')
    sys.path.insert(0, target_dir)

    from evaluator.utils import extract_best_results, evaluate_model
    
    experiment_name = "hit"  # Change as needed

    extract_best_results(data_path=data_path, experiment_name=experiment_name, evalutor="test_error")

    evaluate_model(data_path=data_path, experiment_name=experiment_name, device='cpu', seed=0)

if __name__ == "__main__":
    data_path = "/mnt/d/u_deepflame_agent/hit-best"  # Change as needed
    xde_inference(data_path)