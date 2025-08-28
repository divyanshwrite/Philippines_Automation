import logging
import fitz  # PyMuPDF

logging.basicConfig(level=logging.INFO)

class Extractor:
    def extract_text(self, pdf_path):
        try:
            doc = fitz.open(pdf_path)
            text = "\n".join(page.get_text() for page in doc)
            doc.close()
            return text
        except Exception as e:
            logging.warning(f"Text extraction failed for {pdf_path}: {e}")
            return ""
