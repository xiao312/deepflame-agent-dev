import os
import sys
import json
import shutil
from pathlib import Path

from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

# Register DF_AGENT_ROOT in sys.path
DF_AGENT_ROOT = Path(__file__).resolve().parent
os.environ['DF_AGENT_ROOT'] = str(DF_AGENT_ROOT)

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from dfa_tools import (
    check_bashrc_loaded,
    run_allrun_script,
    read_and_save_openfoam_scalars,
    plot_openfoam_data,
    copy_from_standard,
    initialize_task_manager,
    initialize_tasks,
)
from xdebench_interface.xde_tools import xde_inference_tool

load_dotenv(os.path.join(os.path.dirname(__file__),'.env')) #api,这里的apikey 通过.env注入
os.environ['DEEPSEEK_API_KEY'] = "sk-d78218515ab846eabceb88b48437fcb6"
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))


async def send_image_tool(file_path: str, port: int = 50002) -> str:
    """Prepare the Markdown link for display using a local web server image path."""
    if not os.path.isfile(file_path):
        return json.dumps({"error": "File not found."})

    try:
        # Define the static images directory
        images_dir = Path("/home/xk/Software/6_bohr_agent/src/images")  # Update with your images directory
        images_dir.mkdir(parents=True, exist_ok=True)  # Create the directory if it doesn't exist

        # Copy the image to the static images directory
        filename = os.path.basename(file_path)
        destination_path = images_dir / filename

        shutil.copy(file_path, destination_path)  # Copy the file

        # Construct the URL for the local web server
        local_url = f"http://localhost:{port}/images/{filename}"

        # Prepare the Markdown link for display
        markdown_link = f"![可选的替代文字]({local_url})"

        return json.dumps({
            "message": "Image loaded and copied successfully.",
            "markdown_link": markdown_link
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

async def send_image_from_url(image_url: str) -> str:
    """Prepare the Markdown link for an image directly from a URL."""
    try:
        # Prepare the Markdown link for display
        markdown_link = f"![可选的替代文字]({image_url})"

        return json.dumps({
            "message": "Image link prepared successfully.",
            "markdown_link": markdown_link
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


# def load_simulation_types() -> str:
#     """
#     Load the types of simulations the agent is currently capable of.

#     Returns:
#         JSON string with available simulation types.
#     """

#     # Define the available simulation types
#     simulation_types = {
#         "type_1": {
#             "name": "One-Dimensional Planar Flame",
#             "description": "The case simulates the steady-state 1D freely-propagating flame."
#         },
#         "type_2": {
#             "name": "Two-Dimensional Triple Flame",
#             "description": "This case simulates the evolution of a 2D non-premixed planar jet flame to validate the capability of our solver for multi-dimensional applications."
#         },
#         "type_3": {
#             "name": "Two-Dimensional Reactive Taylor-Green Vortex",
#             "description": "2D reactive Taylor-Green Vortex (TGV) which is simplified from the 3D reactive TGV below is simulated here."
#         },
#         # Add more simulation types as needed
#     }
    
#     # Convert the simulation types to a JSON string
#     return json.dumps(simulation_types, indent=2)

def create_agent(ak=None, app_key=None, project_id=None):
    """SDK标准接口"""
    
    # 创建Agent, 这里需要返回google adk agent, 相当于过去的root_agent
    return LlmAgent(
        name="deepflame_agent_dev_v1",
        model=LiteLlm(model="deepseek/deepseek-chat"),
        instruction="You are a knowledgeable assistant for DeepFlame simulations. "
                    "When the user requests to run a simulation, "
                    "utilize the appropriate tools to set up and execute the simulation. "
                    "If any errors occur during the process, provide a clear and polite explanation. "
                    "Upon successful completion, present the results and visualizations in an organized manner.",
        tools=[
            # load_simulation_types,
            send_image_tool,
            send_image_from_url,
            
            check_bashrc_loaded,
            run_allrun_script,
            read_and_save_openfoam_scalars,
            plot_openfoam_data,

            copy_from_standard,
            
            initialize_task_manager,
            initialize_tasks,
            
            xde_inference_tool,
        ]
    )