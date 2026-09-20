import io
import json
from pathlib import Path


TEXT_EXTENSIONS = {
    ".txt",
    ".md",
    ".csv",
    ".json",
    ".py",
    ".yaml",
    ".yml",
    ".html",
    ".css",
    ".js",
    ".ts",
}


def extract_file_text(filename: str, file_bytes: bytes) -> str:
    """Extract text from common document and source-file formats."""
    extension = Path(filename).suffix.lower()

    if extension in TEXT_EXTENSIONS:
        text = file_bytes.decode("utf-8", errors="replace")
        if extension == ".json":
            try:
                return json.dumps(json.loads(text), indent=2)
            except json.JSONDecodeError:
                return text
        return text

    if extension == ".pdf":
        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)

    if extension == ".docx":
        from docx import Document

        document = Document(io.BytesIO(file_bytes))
        return "\n".join(paragraph.text for paragraph in document.paragraphs)

    raise ValueError(
        "Unsupported file type. Upload a text, code, JSON, PDF, or DOCX file."
    )
