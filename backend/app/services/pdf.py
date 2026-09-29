import io
import re
import pdfplumber

def extract_text_from_pdf(file_bytes: bytes) -> str:
    """
    Extracts text from a PDF byte stream using pdfplumber.
    Cleans unnecessary whitespace and basic formatting.
    """
    text = ""
    try:
        with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
    except Exception as e:
        raise ValueError(f"Failed to read PDF file: {str(e)}")

    # Clean double spaces, tabs, and duplicate linebreaks
    text = re.sub(r'[ \t]+', ' ', text)
    text = re.sub(r'\n\s*\n', '\n', text)
    
    # Return cleaned text stripped of outer spacing
    return text.strip()
