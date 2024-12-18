import aiohttp
import asyncio
from sse_invoke_methods.sse_invoke import SSEInvokeModel

class ReceiveSSEInvokeModelOnlyText:
    def __init__(self, response_sse_message=None, default_url="http://guyan.zzux.com:15499/v1/chat/completions"):
        self.response_sse_message = response_sse_message
        self.default_url = default_url

    @classmethod
    async def new(cls, token, message):
        instance = cls()
        
        await instance.send_request_and_wait(token, message)
        return instance

    async def send_request_and_wait(self, token, message):
        result = SSEInvokeModel.sse_request(token, message, self.default_url)
        try:
            response =  await result
            self.response_sse_message = response
        except Exception as err:
            print(f"Error: {err}")

    def get_response_message(self):
        return self.response_sse_message