from zhipuai import ZhipuAI
import os

# api_key="406773a5a6538f775f57c948dec260b5.KSH5emqhotJLsqe2"
client = ZhipuAI(api_key=os.getenv("ZHIPU_API_KEY"))

def get_response_zhipu(prompt):
    model = "glm-4-plus"
    try:
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )
        # 解析并返回结果
        return response.choices[0].message.content
    except Exception as e:
        # 捕获异常并返回错误消息
        return f"请求出错: {e}"

if __name__ == "__main__":
    prompt = "你是谁"
    result = get_response_zhipu(prompt)
    print(result)