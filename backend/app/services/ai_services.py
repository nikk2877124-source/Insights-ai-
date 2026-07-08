from app.core.ollama import OllamaClient


class AIService:
    """Service responsible for interacting with the AI model."""

    def __init__(self):
        self.ollama = OllamaClient()

    def generate_response(self, prompt: str) -> str:
        """Send a prompt to Ollama and return the generated response."""
        return self.ollama.generate(prompt)

    def generate_dataset_summary(self, profile: dict) -> str:
        """Generate a business-friendly dataset summary from a dataset profile."""
        if not isinstance(profile, dict):
            raise TypeError("profile must be a dictionary")

        # Profile expected shape (based on ProfilingService.generate_profile):
        # - summary: { total_rows, total_columns, missing_values, duplicate_rows, outlier_count, quality_score, grade, status }
        # - details: ...
        # But we defensively support flattened or partially-populated structures.
        summary = profile.get("summary") if isinstance(profile.get("summary"), dict) else profile

        total_rows = summary.get("total_rows")
        total_columns = summary.get("total_columns")
        missing_values = summary.get("missing_values")
        duplicate_rows = summary.get("duplicate_rows")
        outlier_count = summary.get("outlier_count")
        quality_score = summary.get("quality_score")
        grade = summary.get("grade")
        status = summary.get("status")

        prompt = (
            "You are a Senior Data Analyst.\n\n"
            "Write a concise business-friendly summary.\n\n"
            "Use 3–5 sentences.\n"
            "Mention data quality.\n"
            "Mention whether cleaning is recommended.\n"
            "Do not invent information.\n"
            "Do not use markdown.\n\n"
            "Dataset profile metrics:\n"
            f"Total Rows: {total_rows}\n"
            f"Total Columns: {total_columns}\n"
            f"Missing Values: {missing_values}\n"
            f"Duplicate Rows: {duplicate_rows}\n"
            f"Outlier Count: {outlier_count}\n"
            f"Quality Score: {quality_score}\n"
            f"Grade: {grade}\n"
            f"Status: {status}\n"
        )

        return self.ollama.generate(prompt)
