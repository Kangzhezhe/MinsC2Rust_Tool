import asyncio
from models.deepseek import get_response_deepseek, get_response_siliconflow_deepseek
from models.zhipu import get_response_zhipu
from models.local import get_response_from_model
from models.qianwen import get_response_qianwen

def generate_response(prompt,llm_model='qwen',temperature=0.0):
    if llm_model == "local":
        response = asyncio.run(get_response_from_model(prompt))
    elif llm_model == "qwen":
        response = get_response_qianwen(prompt,temperature)
    elif llm_model == "deepseek":
        # response = get_response_deepseek(prompt,temperature)
        response = get_response_siliconflow_deepseek(prompt,temperature)
    elif llm_model == "zhipu":
        response = get_response_zhipu(prompt)
    return response
