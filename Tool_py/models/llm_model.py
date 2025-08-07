import asyncio
from models.deepseek import get_response_deepseek, get_response_siliconflow_deepseek,get_chat_response
from models.zhipu import get_response_zhipu
from models.local import get_response_from_model
from models.qianwen import get_response_qianwen, process_completion_qwq
from models.claude import get_response_claude
from models.gpt import get_response_gpt4o
from utils import extract_rust_code

def generate_response(prompt,llm_model='qwen',temperature=0.0,response_format='text',max_prompt_length=30000):
    if len(prompt) > max_prompt_length:
        return "上下文长度超过限制"
    if llm_model == "local":
        response = asyncio.run(get_response_from_model(prompt))
    elif llm_model == "qwen":
        response = get_response_qianwen(prompt,temperature=temperature,response_format=response_format)
        # response = process_completion_qwq(prompt,temperature=temperature)
    elif llm_model == "deepseek":
        response = get_response_deepseek(prompt,temperature)
        # response = get_response_siliconflow_deepseek(prompt,temperature)
        # response = get_chat_response(prompt,temperature)
    elif llm_model == "zhipu":
        response = get_response_zhipu(prompt)
    elif llm_model == "claude":
        response = get_response_claude(prompt,temperature=temperature,response_format=response_format)
    elif llm_model == "gpt4o":
        response = get_response_gpt4o(prompt,temperature=temperature)

    # if '```rust' in response:
    #     rust_code = extract_rust_code(response)
    #     if rust_code:
    #         response = rust_code

    return response
