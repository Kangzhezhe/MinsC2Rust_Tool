# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI
import os

import requests

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), 
                base_url="https://api.deepseek.com")

def get_response_deepseek(prompt,temperature=0):
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[
            {"role": "user", "content": prompt},
        ],
        stream=False,
        max_tokens=8192,
        temperature=temperature
    )

    return response.choices[0].message.content


def get_response_siliconflow_deepseek(prompt, temperature=0):
    url = "https://api.siliconflow.cn/v1/chat/completions"

    payload = {
        "model": "deepseek-ai/DeepSeek-V3",
        "temperature": temperature,
        "messages": [
            {
                "content": prompt,
                "role": "user"
            }
        ]
    }
    headers = {
        "Authorization": f"Bearer sk-lxcwxxfxyltcbochqnanomryzxdmzpwkiqkjyisqmallaezv",
        "Content-Type": "application/json"
    }
    for attempt in range(3):
        response = requests.request("POST", url, json=payload, headers=headers)
        response_json = response.json()
        if 'choices' in response_json:
            return response_json['choices'][0]['message']['content']
        else:
            print(f"Attempt {attempt + 1} failed, retrying...")

    # 如果所有重试都失败，返回错误消息
    return "请求失败：未能获取有效响应"



if __name__ == '__main__':
    prompt = "你是谁？"
    response = get_response_siliconflow_deepseek(prompt)
    print(response)