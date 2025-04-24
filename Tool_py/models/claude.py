# -*- coding: utf-8 -*-
import os
from openai import OpenAI

# 初始化客户端（接入 Claude 的 OpenAI 兼容服务）
client = OpenAI(
    api_key="sk-BKFud7klmvuqdIU2pauGEK65tEkLZZ87OeH43almuEMTofGf",
    base_url="https://chat.cloudapi.vip/v1",  # 替换成你 Claude 接口地址
)


# Claude 模型回复函数
def get_response_claude(prompt, response_format='text', temperature=0, max_retries=3):
    try:
        for attempt in range(max_retries):
            request_params = {
                'model': 'claude-3-5-sonnet-20241022',  # Claude 模型名（确认服务支持）
                'messages': [
                    {"role": "user", "content": prompt}
                ],
                'temperature': temperature,
                'timeout': 300
            }

            if response_format == 'json':
                request_params['response_format'] = {"type": "json_object"}

            completion = client.chat.completions.create(**request_params)
            response = completion.choices[0].message.content

            # 检查返回值是否为空字符串
            if response.strip():
                return response
            else:
                print(f"第 {attempt + 1} 次请求返回空字符串，重试中...")

        return "请求出错：多次尝试后仍返回空字符串"
    except Exception as e:
        return f"请求出错: {e}"

# 示例调用
if __name__ == "__main__":
    response = get_response_claude("你是谁")
    print(f"\n🤖 Claude 回复：\n{response}")
