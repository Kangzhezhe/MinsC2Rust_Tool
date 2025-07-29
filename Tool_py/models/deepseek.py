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

import subprocess
import json

def get_chat_response(prompt, temperature=0):
    curl_command = [
        'curl', '-X', 'POST', '--location', 'https://chat.zju.edu.cn/api/ai/v1/chat/completions',
        '--header', 'Content-Type: application/json',
        '--header', 'Authorization: Bearer sk-WGje1bURmsSvnezr92277f75B6B74955A8F3C36c582c28B4',
        '--data', json.dumps({
            "model": "deepseek-v3-671b",
            "messages": [
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt}
            ],
            "stream": False
        })
    ]

    result = subprocess.run(curl_command, capture_output=True, text=True)

    # 解析 JSON 响应
    response_json = json.loads(result.stdout)

    # 获取 content 字段
    if  'choices' not in response_json:
        import ipdb; ipdb.set_trace()
    content = response_json['choices'][0]['message']['content']

    return content

if __name__ == '__main__':
    prompt = "你是谁？"
    response = get_response_siliconflow_deepseek(prompt)
    print(response)