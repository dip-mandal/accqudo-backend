import fitz
import docx
import io


def parse_pdf(file_bytes):

    doc = fitz.open(stream=file_bytes, filetype="pdf")

    text = ""

    for page in doc:
        text += page.get_text()

    return text


def parse_docx(file_bytes):

    doc = docx.Document(io.BytesIO(file_bytes))

    return "\n".join(p.text for p in doc.paragraphs)


def extract_text(filename, file_bytes):

    filename = filename.lower()

    if filename.endswith(".pdf"):
        return parse_pdf(file_bytes)

    if filename.endswith(".docx"):
        return parse_docx(file_bytes)

    raise ValueError("Unsupported file")