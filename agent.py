import os
import json
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from dotenv import load_dotenv

load_dotenv(os.path.join(os.path.dirname(__file__),'.env')) #api,这里的apikey 通过.env注入
os.environ['DEEPSEEK_API_KEY'] = "sk-d78218515ab846eabceb88b48437fcb6"
# os.environ["MOONSHOT_API_KEY"] = "sk-Ec3zvaWu0rgeM9sXt6A7jVlvZbdRL8bYIDlkcK44hU9bKuUe"

def load_simulation_types() -> str:
    """
    Load the types of simulations the agent is currently capable of.

    Returns:
        JSON string with available simulation types.
    """

    # Define the available simulation types
    simulation_types = {
        "type_1": {
            "name": "One-Dimensional Planar Flame",
            "description": "The case simulates the steady-state 1D freely-propagating flame."
        },
        "type_2": {
            "name": "Two-Dimensional Triple Flame",
            "description": "This case simulates the evolution of a 2D non-premixed planar jet flame to validate the capability of our solver for multi-dimensional applications."
        },
        "type_3": {
            "name": "Two-Dimensional Reactive Taylor-Green Vortex",
            "description": "2D reactive Taylor-Green Vortex (TGV) which is simplified from the 3D reactive TGV below is simulated here."
        },
        # Add more simulation types as needed
    }
    
    # Convert the simulation types to a JSON string
    return json.dumps(simulation_types, indent=2)

def create_agent(ak=None, app_key=None, project_id=None):#
    """SDK标准接口"""
    
    # 定义工具函数
    
    def my_tool(param: str):
        """工具描述"""
        return "result"
    
    # 创建Agent, 这里需要返回google adk agent, 相当于过去的root_agent
    return LlmAgent(
        name="my_agent",
        model=LiteLlm(model="deepseek/deepseek-chat"),
        # model=LiteLlm(model="moonshot/moonshot-v1-8k"),
        instruction="Agent 指令",
        tools=[my_tool, load_simulation_types] # 注册工具
    )