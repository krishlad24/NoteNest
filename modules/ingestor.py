"""Multi-Format Document Ingestion Engine for NoteNest.

Parses .pdf, .pptx, and .docx documents into structured, clean Markdown text.
Supports file paths as well as BytesIO / file-like streams (e.g. Streamlit UploadedFile).
"""

import io
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union

import docx
import pymupdf as fitz
import pptx


@dataclass
class DocumentResult:
    """Structured result of document parsing."""
    filename: str
    file_type: str
    markdown: str
    stats: Dict[str, Any] = field(default_factory=dict)
    sections: List[Dict[str, str]] = field(default_factory=list)


class DocumentIngestor:
    """Unified engine to ingest PDF, PPTX, and DOCX documents into clean Markdown."""

    @staticmethod
    def _read_bytes(source: Union[str, bytes, io.BytesIO, Any]) -> bytes:
        """Helper to extract raw bytes from filepath or file-like object."""
        if isinstance(source, bytes):
            return source
        if isinstance(source, str):
            with open(source, "rb") as f:
                return f.read()
        if hasattr(source, "read"):
            current_pos = source.tell() if hasattr(source, "tell") else None
            data = source.read()
            if current_pos is not None and hasattr(source, "seek"):
                source.seek(0)
            return data
        raise ValueError(f"Unsupported source type: {type(source)}")

    @classmethod
    def parse_pdf(cls, source: Union[str, bytes, io.BytesIO, Any], filename: str = "document.pdf") -> DocumentResult:
        """Parse a PDF document using PyMuPDF (fitz) ordered by visual blocks.
        
        Extracts blocks, sorts them in natural visual reading order (top-to-bottom,
        left-to-right), cleans headers/footers where possible, and emits formatted Markdown.
        """
        raw_bytes = cls._read_bytes(source)
        doc = fitz.open(stream=raw_bytes, filetype="pdf")
        
        md_parts = [f"# 📄 Document: {filename}\n"]
        sections = []
        total_pages = len(doc)
        total_words = 0

        for page_idx in range(total_pages):
            page = doc[page_idx]
            page_num = page_idx + 1
            
            # Extract blocks: (x0, y0, x1, y1, text, block_no, block_type)
            # block_type == 0 is text, 1 is image
            blocks = page.get_text("blocks")
            
            # Filter text blocks and sort by visual coordinates
            # We group y coordinates by approximate line bands (~8 points) to preserve multi-column / tabular flow
            text_blocks = [b for b in blocks if b[6] == 0 and b[4].strip()]
            sorted_blocks = sorted(
                text_blocks, 
                key=lambda b: (round(b[1] / 12) * 12, b[0])
            )
            
            page_texts = []
            for b in sorted_blocks:
                content = b[4].strip()
                if not content:
                    continue
                
                # Check if block looks like a prominent heading (short, all caps or title case without ending period)
                lines = [line.strip() for line in content.split("\n") if line.strip()]
                cleaned_block = "\n".join(lines)
                
                if len(lines) == 1 and len(lines[0]) < 80 and not lines[0].endswith((".", ";", ",")):
                    if lines[0].isupper() or len(lines[0]) < 45:
                        page_texts.append(f"### {lines[0]}")
                        continue
                
                page_texts.append(cleaned_block)
            
            page_content = "\n\n".join(page_texts).strip()
            if page_content:
                section_title = f"Page {page_num}"
                section_md = f"## 📖 {section_title}\n\n{page_content}\n"
                md_parts.append(section_md)
                sections.append({"title": section_title, "content": page_content, "page": page_num})
                total_words += len(page_content.split())

        doc.close()
        full_md = "\n".join(md_parts).strip()
        
        return DocumentResult(
            filename=filename,
            file_type="pdf",
            markdown=full_md,
            stats={
                "page_count": total_pages,
                "word_count": total_words,
                "character_count": len(full_md),
                "sections_count": len(sections)
            },
            sections=sections
        )

    @classmethod
    def parse_pptx(cls, source: Union[str, bytes, io.BytesIO, Any], filename: str = "presentation.pptx") -> DocumentResult:
        """Parse a PowerPoint (.pptx) file slide-by-slide preserving structure, bullet hierarchy, and tables."""
        raw_bytes = cls._read_bytes(source)
        prs = pptx.Presentation(io.BytesIO(raw_bytes))
        
        md_parts = [f"# 📊 Presentation: {filename}\n"]
        sections = []
        total_slides = len(prs.slides)
        total_words = 0

        for slide_idx, slide in enumerate(prs.slides):
            slide_num = slide_idx + 1
            slide_title = ""
            
            # Detect title if present
            if slide.shapes.title and slide.shapes.title.has_text_frame:
                slide_title = slide.shapes.title.text.strip()
            
            display_title = slide_title if slide_title else f"Slide {slide_num}"
            slide_lines = []
            
            for shape in slide.shapes:
                # Avoid re-processing the title shape in the body
                if shape == slide.shapes.title:
                    continue
                
                # Extract text frames with indentation / bullet hierarchy
                if shape.has_text_frame:
                    for paragraph in shape.text_frame.paragraphs:
                        p_text = paragraph.text.strip()
                        if not p_text:
                            continue
                        
                        level = paragraph.level or 0
                        indent = "  " * level
                        slide_lines.append(f"{indent}- {p_text}")
                
                # Extract tables
                elif shape.has_table:
                    table = shape.table
                    table_rows = []
                    for row in table.rows:
                        row_cells = [cell.text.strip().replace("\n", " ") for cell in row.cells]
                        table_rows.append(row_cells)
                    
                    if table_rows:
                        # Markdown table formatting
                        header = "| " + " | ".join(table_rows[0]) + " |"
                        divider = "| " + " | ".join(["---"] * len(table_rows[0])) + " |"
                        body_rows = ["| " + " | ".join(r) + " |" for r in table_rows[1:]]
                        slide_lines.append("\n" + "\n".join([header, divider] + body_rows) + "\n")
            
            slide_body = "\n".join(slide_lines).strip()
            section_md = f"## 🖥️ Slide {slide_num}: {display_title}\n\n"
            if slide_body:
                section_md += f"{slide_body}\n"
            else:
                section_md += "*(Visual slide with minimal text)*\n"
            
            md_parts.append(section_md)
            sections.append({"title": f"Slide {slide_num}: {display_title}", "content": slide_body, "slide": slide_num})
            total_words += len((display_title + " " + slide_body).split())

        full_md = "\n".join(md_parts).strip()
        
        return DocumentResult(
            filename=filename,
            file_type="pptx",
            markdown=full_md,
            stats={
                "slide_count": total_slides,
                "word_count": total_words,
                "character_count": len(full_md),
                "sections_count": len(sections)
            },
            sections=sections
        )

    @classmethod
    def parse_docx(cls, source: Union[str, bytes, io.BytesIO, Any], filename: str = "document.docx") -> DocumentResult:
        """Parse a Word (.docx) document paragraph-by-paragraph and table-by-table with Markdown heading fidelity."""
        raw_bytes = cls._read_bytes(source)
        doc = docx.Document(io.BytesIO(raw_bytes))
        
        md_parts = [f"# 📝 Word Document: {filename}\n"]
        sections = []
        current_section_title = "Introduction"
        current_section_content = []
        total_words = 0
        
        # Iterate document elements: paragraphs and tables
        for paragraph in doc.paragraphs:
            text = paragraph.text.strip()
            if not text:
                continue
            
            style_name = paragraph.style.name.lower() if paragraph.style and paragraph.style.name else ""
            
            if "heading 1" in style_name:
                if current_section_content:
                    sections.append({"title": current_section_title, "content": "\n\n".join(current_section_content)})
                    current_section_content = []
                current_section_title = text
                md_parts.append(f"\n## 📌 {text}\n")
            elif "heading 2" in style_name:
                md_parts.append(f"\n### {text}\n")
                current_section_content.append(f"### {text}")
            elif "heading 3" in style_name:
                md_parts.append(f"\n#### {text}\n")
                current_section_content.append(f"#### {text}")
            elif "bullet" in style_name or "list" in style_name:
                md_parts.append(f"- {text}")
                current_section_content.append(f"- {text}")
            elif "title" in style_name:
                md_parts.append(f"\n# {text}\n")
                current_section_title = text
            else:
                md_parts.append(f"{text}\n")
                current_section_content.append(text)
            
            total_words += len(text.split())
        
        # Extract tables
        for table_idx, table in enumerate(doc.tables):
            table_rows = []
            for row in table.rows:
                cells = [c.text.strip().replace("\n", " ") for c in row.cells]
                table_rows.append(cells)
            
            if table_rows:
                header = "| " + " | ".join(table_rows[0]) + " |"
                divider = "| " + " | ".join(["---"] * len(table_rows[0])) + " |"
                body = ["| " + " | ".join(r) + " |" for r in table_rows[1:]]
                table_md = "\n" + "\n".join([header, divider] + body) + "\n"
                md_parts.append(table_md)
                current_section_content.append(table_md)

        if current_section_content:
            sections.append({"title": current_section_title, "content": "\n\n".join(current_section_content)})

        full_md = "\n".join(md_parts).strip()
        
        return DocumentResult(
            filename=filename,
            file_type="docx",
            markdown=full_md,
            stats={
                "paragraph_count": len(doc.paragraphs),
                "table_count": len(doc.tables),
                "word_count": total_words,
                "character_count": len(full_md),
                "sections_count": len(sections)
            },
            sections=sections
        )

    @classmethod
    def ingest_file(cls, source: Union[str, bytes, io.BytesIO, Any], filename: Optional[str] = None) -> DocumentResult:
        """Unified entry point to ingest any supported document (.pdf, .pptx, .docx)."""
        resolved_filename = filename
        if not resolved_filename and isinstance(source, str):
            resolved_filename = os.path.basename(source)
        elif not resolved_filename and hasattr(source, "name"):
            resolved_filename = getattr(source, "name")
        
        if not resolved_filename:
            resolved_filename = "document"

        ext = os.path.splitext(resolved_filename)[1].lower()
        if ext == ".pdf":
            return cls.parse_pdf(source, filename=resolved_filename)
        elif ext in (".pptx", ".ppt"):
            return cls.parse_pptx(source, filename=resolved_filename)
        elif ext in (".docx", ".doc"):
            return cls.parse_docx(source, filename=resolved_filename)
        else:
            raise ValueError(f"Unsupported file format '{ext}'. NoteNest supports .pdf, .pptx, and .docx files.")
