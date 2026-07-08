from app.core.ollama import OllamaClient


class AIService:
    """
    Service responsible for interacting with the AI model.
    """

    def __init__(self):
        self.ollama = OllamaClient()

    def generate_response(self, prompt: str) -> str:
        """
        Send a prompt to Ollama and return the generated response.
        """
        return self.ollama.generate(prompt)