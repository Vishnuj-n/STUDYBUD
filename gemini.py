import os
import pathlib
from google import genai
from google.genai import types
from dotenv import load_dotenv

class KeyConceptExtractor:
    def __init__(self, api_key_env: str = "GEMINI_API_KEY"):
        load_dotenv()
        api_key = os.getenv(api_key_env)
        if not api_key:
            raise ValueError(f"API key not found in environment variable '{api_key_env}'")
        self.client = genai.Client(api_key=api_key)
        self.model = "gemini-2.5-flash"
        self.prompt = (
            "Identify the key concepts discussed in this document. "
            "Return them as a Python list of strings like: "
            "['Concept 1', 'Concept 2', 'Concept 3']"
        )

    def extract_from_pdf(self, pdf_path: str) -> str:
        path = pathlib.Path(pdf_path)
        if not (path.exists() and path.suffix == ".pdf"):
            raise FileNotFoundError(f"Invalid PDF path: {pdf_path}")
        
        # Read PDF bytes
        pdf_bytes = path.read_bytes()
        
        # Create Part objects properly using the types module
        pdf_part = types.Part(
            inline_data=types.Blob(
                mime_type="application/pdf",
                data=pdf_bytes
            )
        )
        
        # Send to Gemini API
        return self.client.models.generate_content(
            model=self.model,
            contents=[pdf_part, self.prompt]
        ).text
