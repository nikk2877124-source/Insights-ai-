from ollama import Client


class OllamaClient:
    """
    Handles communication with the local Ollama server.
    """

    def __init__(self):
        self.client = Client(host="http://localhost:11434")
        self.model = "qwen3.5:latest"

    def generate(self, prompt: str) -> str:
        """
        Send a prompt to Ollama and return the response.
        """
        response = self.client.generate(
            model=self.model,
            prompt=prompt
        )

        return response["response"]