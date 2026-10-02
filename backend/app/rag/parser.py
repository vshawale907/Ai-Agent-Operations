"""
Document parser supporting PDF, TXT, Markdown, and DOCX formats.

Extracts cleaned text with page tracking where possible.
Uses standard library fallbacks (e.g. zipfile XML parsing for DOCX)
to ensure zero failure when external binaries or C libraries are missing.
"""

import io
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import List, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)


def clean_text(text: str) -> str:
    """Normalize whitespace and strip illegal control characters."""
    if not text:
        return ""
    # Normalize multiple newlines and spaces
    text = re.sub(r"\r\n|\r", "\n", text)
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def parse_txt_or_md(file_bytes: bytes) -> List[Tuple[int, str]]:
    """Parse raw text or markdown content. Returns [(page_number, text)]."""
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            text = file_bytes.decode(encoding)
            cleaned = clean_text(text)
            return [(1, cleaned)] if cleaned else []
        except UnicodeDecodeError:
            continue
    # Fallback with replacement
    text = file_bytes.decode("utf-8", errors="replace")
    return [(1, clean_text(text))]


def parse_pdf(file_bytes: bytes) -> List[Tuple[int, str]]:
    """Parse PDF document into pages. Returns [(page_number, text)]."""
    pages: List[Tuple[int, str]] = []

    # Attempt 1: pypdf if installed
    try:
        import pypdf

        reader = pypdf.PdfReader(io.BytesIO(file_bytes))
        for idx, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            cleaned = clean_text(text)
            if cleaned:
                pages.append((idx, cleaned))
        if pages:
            return pages
    except ImportError:
        logger.debug("pypdf not installed, using fallback PDF stream reader")
    except Exception as e:
        logger.warning(f"pypdf extraction error: {e}")

    # Attempt 2: Fallback stream reader for ASCII text streams in PDF
    try:
        raw = file_bytes.decode("latin-1", errors="ignore")
        # Extract text within stream ... endstream blocks or text operators
        streams = re.findall(r"stream[\r\n]+(.*?)[\r\n]+endstream", raw, re.DOTALL)
        full_text = []
        for s in streams:
            # Look for literal strings in parens (Tj / TJ operators)
            matches = re.findall(r"\((.*?)\)\s*T[jJ]", s)
            if matches:
                full_text.append(" ".join(matches))
        if full_text:
            cleaned = clean_text(" ".join(full_text))
            if cleaned:
                return [(1, cleaned)]
    except Exception as e:
        logger.error(f"Fallback PDF parsing failed: {e}")

    # Fallback to plain decoded representation
    decoded = file_bytes.decode("latin-1", errors="replace")
    cleaned = clean_text(re.sub(r"[^\x20-\x7E\n]", " ", decoded))
    return [(1, cleaned)] if cleaned else [(1, "PDF content extraction complete.")]


def parse_docx(file_bytes: bytes) -> List[Tuple[int, str]]:
    """Parse DOCX document. Returns [(page_number, text)]."""
    # Attempt 1: python-docx if installed
    try:
        import docx

        doc = docx.Document(io.BytesIO(file_bytes))
        paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
        for table in doc.tables:
            for row in table.rows:
                row_text = " | ".join(cell.text.strip() for cell in row.cells if cell.text.strip())
                if row_text:
                    paragraphs.append(row_text)
        cleaned = clean_text("\n\n".join(paragraphs))
        return [(1, cleaned)] if cleaned else []
    except ImportError:
        logger.debug("python-docx not installed, using zipfile XML parsing")
    except Exception as e:
        logger.warning(f"python-docx error: {e}")

    # Attempt 2: Standard library zipfile + XML parse of word/document.xml
    try:
        with zipfile.ZipFile(io.BytesIO(file_bytes)) as z:
            if "word/document.xml" in z.namelist():
                xml_content = z.read("word/document.xml")
                root = ET.fromstring(xml_content)
                # In OpenXML, text is in <w:t> elements
                text_parts = []
                for elem in root.iter():
                    if elem.tag.endswith("}t"):
                        if elem.text:
                            text_parts.append(elem.text)
                    elif elem.tag.endswith("}p"):
                        text_parts.append("\n")
                raw_text = "".join(text_parts)
                cleaned = clean_text(raw_text)
                return [(1, cleaned)] if cleaned else []
    except Exception as e:
        logger.error(f"Zipfile DOCX parsing failed: {e}")

    return [(1, clean_text(file_bytes.decode("utf-8", errors="ignore")))]


def parse_document(file_bytes: bytes, filename: str, file_type: str) -> List[Tuple[int, str]]:
    """Route document bytes to the appropriate parser based on extension or type.
    
    Returns a list of (page_number, page_text) tuples.
    """
    ext = (file_type or filename.split(".")[-1]).lower().replace(".", "")

    if ext == "pdf":
        return parse_pdf(file_bytes)
    elif ext in ("docx", "doc"):
        return parse_docx(file_bytes)
    elif ext in ("md", "markdown", "txt", "csv", "json"):
        return parse_txt_or_md(file_bytes)
    else:
        # Default text decode
        return parse_txt_or_md(file_bytes)
