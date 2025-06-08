import os
import pathlib
from google import genai
from google.genai import types


class KeyConceptExtractor:
    def __init__(self, api_key_env: str = "GEMINI_API_KEY"):
        api_key = os.environ.get(api_key_env)
        if not api_key:
            raise ValueError(f"API key not found in environment variable '{api_key_env}'")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.0-flash"
        self.default_prompt = (
            "Identify the key concepts discussed in this document. Present them as a Python list of strings. "
            "For example: the key concepts are: ['Concept 1', 'Concept 2', 'Concept 3']"
        )

    def extract_from_pdf(self, pdf_path: str) -> str:
        """Extract key concepts from a PDF file."""
        path = pathlib.Path(pdf_path)
        if not path.exists() or not path.suffix == ".pdf":
            raise FileNotFoundError(f"Invalid PDF file path: {pdf_path}")

        response = self.client.models.generate_content(
            model=self.model,
            contents=[
                types.Part.from_bytes(
                    data=path.read_bytes(),
                    mime_type='application/pdf',
                ),
                self.default_prompt
            ]
        )
        return response.text

    def extract_from_text(self, text: str) -> str:
        """Extract key concepts from plain text."""
        if not text.strip():
            raise ValueError("Input text is empty.")
        response = self.client.models.generate_content(
            model=self.model,
            contents=text
        )
        return response.text


