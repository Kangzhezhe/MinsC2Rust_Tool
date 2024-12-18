
from sse_invoke_method import ReceiveSSEInvokeModelOnlyText
from sse_invoke_methods.sse_invokes.constant_value import API_KEY
class C2RustGLM:
    def __init__(self):
        self.chatglm_response = ""

    async def sse_invoke_calling(self, api_key, user_input):
        sse_call = await ReceiveSSEInvokeModelOnlyText.new(api_key, user_input.strip())
        self.chatglm_response = sse_call.get_response_message() or "Error: Unable to get SSE response."

    def get_ai_response(self):
        return self.chatglm_response

c_2_rust_glm = C2RustGLM()

async def get_response_from_model(prompt):
    await c_2_rust_glm.sse_invoke_calling(API_KEY, prompt)
    response = c_2_rust_glm.get_ai_response()
    return response