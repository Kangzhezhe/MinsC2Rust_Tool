import requests
import json

API_KEY = "sk-mwxoTPKbwt2H8WBrX4YDiEOuaSb7MAlMu0xodUiWd2bvImF6"
API_URL = "https://api.nuwaapi.com/v1/chat/completions"  # 完整路径

def get_response_gpt4o(prompt, temperature=0):
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {API_KEY}"
    }

    payload = {
        "model": "gpt-4o",
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        "temperature": temperature
    }

    try:
        response = requests.post(API_URL, headers=headers, json=payload)
        response.raise_for_status()
        data = response.json()
        return data['choices'][0]['message']['content']
    except Exception as e:
        return f"请求出错:\n{e}"

# 示例调用
if __name__ == "__main__":
    response = get_response_gpt4o("你好！")
    print(response)
