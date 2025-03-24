import os
from openai import OpenAI

# os.environ["DASHSCOPE_API_KEY"] = "sk-85bbe2a2be41434593340a7c1c54aee9"

client = OpenAI(
    api_key=os.getenv("QWEN_API_KEY"), 
    base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
)

def get_response_qianwen(prompt, response_format='text', temperature=0):
    try:
        request_params = {
            'model': 'deepseek-v3',  # 模型列表：https://help.aliyun.com/zh/model-studio/getting-started/models
            'messages': [{'role': 'user', 'content': prompt}],
            'temperature': temperature,
            'timeout': 300
        }
        
        if response_format == 'json':
            request_params['response_format'] = {"type": "json_object"}
        
        completion = client.chat.completions.create(**request_params)
        return completion.choices[0].message.content
    except Exception as e:
        # 捕获异常并返回错误消息
        return f"请求出错: {e}"


def process_completion_qwq(question,response_format='text', temperature=0):
     # 创建聊天完成请求
    completion = client.chat.completions.create(
        model="qwq-plus",  # 此处以 qwq-32b 为例，可按需更换模型名称
        messages=[
            {"role": "user", "content": question}
        ],
        stream=True,
        temperature=temperature
        # 解除以下注释会在最后一个chunk返回Token使用量
        # stream_options={
        #     "include_usage": True
        # }
    )

    reasoning_content = ""  # 定义完整思考过程
    answer_content = ""     # 定义完整回复
    is_answering = False   # 判断是否结束思考过程并开始回复

    for chunk in completion:
        # 如果chunk.choices为空，则打印usage
        if not chunk.choices:
            print("\nUsage:")
            print(chunk.usage)
        else:
            delta = chunk.choices[0].delta
            # 打印思考过程
            if hasattr(delta, 'reasoning_content') and delta.reasoning_content is not None:
                print(delta.reasoning_content, end='', flush=True)
                reasoning_content += delta.reasoning_content
            else:
                # 开始回复
                if delta.content != "" and is_answering is False:
                    # print("\n" + "=" * 20 + "完整回复" + "=" * 20 + "\n")
                    is_answering = True
                # 打印回复过程
                # print(delta.content, end='', flush=True)
                answer_content += delta.content

    # print("=" * 20 + "完整思考过程" + "=" * 20 + "\n")
    # print(reasoning_content)
    # print("=" * 20 + "完整回复" + "=" * 20 + "\n")
    # print(answer_content)
    return answer_content

if __name__ == '__main__':
    prompt = "你是谁？"
    response = get_response_qianwen(prompt)
    print(response)