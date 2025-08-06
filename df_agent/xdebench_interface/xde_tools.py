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
    if not isinstance(data_path, str) or not data_path:
        return {"status": "error", "error_message": "Invalid data path provided."}

    try:
        # Call the existing xde_inference function
        xde_inference(data_path)
        return {"status": "success", "message": "Inference completed successfully."}
    except Exception as e:
        return {"status": "error", "error_message": str(e)}
