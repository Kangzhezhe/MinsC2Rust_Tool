# Please install OpenAI SDK first: `pip3 install openai`

from openai import OpenAI
import os

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), 
                base_url="https://api.deepseek.com")

def get_response_deepseek(prompt):
    response = client.chat.completions.create(
        model="deepseek-coder",
        messages=[
            {"role": "user", "content": prompt},
        ],
        stream=False,
        temperature = 0,
    )

    return response.choices[0].message.content

if __name__ == '__main__':
    prompt = "你是谁？"
    response = get_response_deepseek(prompt)
    print(response)