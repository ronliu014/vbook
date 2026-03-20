import litellm
from ..base import LLMBackend

class LiteLLMBackend(LLMBackend):
    def __init__(self, model: str, base_url: str = None):
        self.model = model
        self.base_url = base_url

    def analyze(self, text: str, prompt: str) -> str:
        kwargs = {"model": self.model, "messages": [
            {"role": "system", "content": prompt},
            {"role": "user", "content": text},
        ]}
        if self.base_url:
            kwargs["api_base"] = self.base_url
        response = litellm.completion(**kwargs)
        return response.choices[0].message.content