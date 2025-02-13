import os
from openai import OpenAI

# os.environ["DASHSCOPE_API_KEY"] = "sk-85bbe2a2be41434593340a7c1c54aee9"

client = OpenAI(
    api_key=os.getenv("QWEN_API_KEY"), 
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def get_response_qianwen(prompt, response_format='text', temperature=0):
    try:
        completion = client.chat.completions.create(
            # model="qwen-coder-plus", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            model="deepseek-v3", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            # model="qwen-max", # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            messages=[
                {'role': 'user', 'content': prompt}],
            temperature=temperature,
            timeout=1000,
        )
        return completion.choices[0].message.content
    except Exception as e:
        # 捕获异常并返回错误消息
        return f"请求出错: {e}"

if __name__ == '__main__':
    prompt = "你是谁？"
    response = get_response_qianwen(prompt)
    print(response)