import io

import pdfplumber

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """Extract full text from a PDF file."""
    text_parts: list[str] = []
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)
    return "\n\n".join(text_parts)


def extract_text_from_txt(file_bytes: bytes) -> str:
    """Decode plain-text file, trying utf-8 then latin-1 as fallback."""
    try:
        return file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        return file_bytes.decode("latin-1")


def extract_text(filename: str, file_bytes: bytes) -> str:
    """Dispatch text extraction based on file extension."""
    lower = filename.lower()
    if lower.endswith(".pdf"):
        return extract_text_from_pdf(file_bytes)
    if lower.endswith(".txt"):
        return extract_text_from_txt(file_bytes)
    raise ValueError(f"Unsupported file type: {filename}")
