import re
import json
import asyncio
import aiohttp
from collections import deque
from .sse_invokes.constant_value import LANGUAGE_MODEL, SYSTEM_CONTENT, SYSTEM_ROLE, USER_ROLE, TEMP_FLOAT, TOP_P_FLOAT, ASSISTANT_ROLE
from .sse_invokes.history_message import HistoryMessage

UNICODE_REGEX = re.compile(r"\\u[0-9a-fA-F]{4}")

class MessageProcessor:
    def __init__(self, user_role):
        self.messages = HistoryMessage()
        self.user_role = user_role

    def set_input_message(self):
        message = self.messages.load_history_from_file()
        return message if message else None

    def last_messages(self, role, messages):
        input_message = self.set_input_message() or ""
        # input_data = json.loads(input_message) if input_message else {}
        input_data = {}
        
        input_data["role"] = role
        input_data["content"] = messages
        texts = json.dumps(input_data)
        user_messages = input_message + texts
        result = re.sub(r",(\s*})", "", user_messages)
        return result

class SSEInvokeModel:
    def __init__(self):
        self.get_message = ""
        self.ai_response_data = ""

    @staticmethod
    async def sse_request(token, input, default_url):
        sse_invoke_model = SSEInvokeModel()
        await SSEInvokeModel.sse_invoke_request_method(sse_invoke_model, token, input, default_url)
        response_message = sse_invoke_model.ai_response_data
        result = sse_invoke_model.process_sse_message(response_message, input)
        return result

    @staticmethod
    async def generate_sse_json_request_body(language_model, system_role, system_content, user_role, user_input, temp_float, top_p_float):
        message_process = MessageProcessor(user_role)
        messages = [
            {"role": system_role, "content": system_content},
            {"role": user_role, "content": message_process.last_messages(user_role, user_input)}
        ]
        options = {"num_ctx": 16000}
        json_request_body = {
            "model": language_model,
            "messages": messages,
            "stream": True,
            "do_sample": True,
            "temperature": temp_float,
            "top_p": top_p_float,
            "options": options
        }
        json_string = json.dumps(json_request_body)
        result = json_string.replace(r"\\\\", r"\\").replace(r"\\", r"").strip()
        return result

    @staticmethod
    async def sse_invoke_request_method(self, token, user_input, default_url):
        json_content = await SSEInvokeModel.generate_sse_json_request_body(
            LANGUAGE_MODEL, SYSTEM_ROLE, SYSTEM_CONTENT.strip(), USER_ROLE, user_input, TEMP_FLOAT, TOP_P_FLOAT
        )
        async with aiohttp.ClientSession() as session:
            async with session.post(default_url, headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "Accept": "text/event-stream",
                "Content-Type": "application/json;charset=UTF-8",
                "Authorization": f"Bearer {token}"
            }, data=json_content, timeout=180) as response:
                if response.status != 200:
                    raise Exception(f"Server returned an error: {response.status}")
                sse_data = ""
                async for chunk in response.content.iter_any():
                    data = chunk.decode('utf-8')
                    sse_data += data
                    self.ai_response_data = sse_data
                    if "data: [DONE]" in data:
                        break
                return sse_data

    def process_sse_message(self, response_data, user_message):
        char_queue = deque()
        queue_result = ""
        json_messages = [line.strip().lstrip("data: ") for line in response_data.splitlines() if line.strip()]
        for json_message in json_messages:
            if json_message == "[DONE]":
                break
            try:
                json_element = json.loads(json_message)
                choices = json_element.get("choices", [])
                if choices:
                    delta = choices[0].get("delta", {})
                    content = delta.get("content", "")
                    get_message = self.convert_unicode_emojis(content).replace("\"", "").replace("\\n\\n", "\n").replace("\\nn", "\n").replace("\\\\n", "\n").replace("\\\\nn", "\n").replace("\\", "")
                    # get_message = content.replace("\"", "").replace("\\n\\n", "\n").replace("\\nn", "\n").replace("\\\\n", "\n").replace("\\\\nn", "\n").replace("\\", "")
                    char_queue.extend(get_message)
            except json.JSONDecodeError:
                print(f"Error reading JSON: {json_message}")
        queue_result = ''.join(char_queue)
        if queue_result:
            message_process = HistoryMessage()
            # message_process.add_history_to_file(USER_ROLE, user_message)
            # message_process.add_history_to_file(ASSISTANT_ROLE, queue_result)
        return queue_result

    @staticmethod
    def convert_unicode_emojis(input_str):
        return UNICODE_REGEX.sub(lambda match: chr(int(match.group(0)[2:], 16)), input_str)

    def response_sse_message(self):
        return self.get_message