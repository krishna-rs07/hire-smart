"""
Resume Parser Module
Handles text extraction from PDF and DOCX files.
"""

import re
import logging
from pathlib import Path
from typing import Optional, Tuple

import fitz  # PyMuPDF
from docx import Document

logger = logging.getLogger(__name__)


class ResumeParser:
    """Extract text content from resume files (PDF/DOCX)."""

    def __init__(self):
        self.supported_extensions = {'.pdf', '.docx'}

    def extract_text(self, file_path: str) -> Tuple[str, dict]:
        """
        Extract text from a resume file.

        Args:
            file_path: Path to the resume file

        Returns:
            Tuple of (extracted_text, metadata)
            metadata includes: file_type, page_count, char_count, extraction_method
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        if extension not in self.supported_extensions:
            raise ValueError(f"Unsupported file format: {extension}. Supported: PDF, DOCX")

        if extension == '.pdf':
            return self._extract_from_pdf(file_path)
        elif extension == '.docx':
            return self._extract_from_docx(file_path)

    def _extract_from_pdf(self, file_path: str) -> Tuple[str, dict]:
        """Extract text from PDF using PyMuPDF."""
        text_parts = []
        metadata = {
            'file_type': 'pdf',
            'page_count': 0,
            'char_count': 0,
            'extraction_method': 'PyMuPDF'
        }

        try:
            doc = fitz.open(file_path)
            metadata['page_count'] = len(doc)

            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text()
                if text.strip():
                    text_parts.append(text)

            doc.close()

            full_text = '\n\n'.join(text_parts)
            metadata['char_count'] = len(full_text)

            # Clean up the extracted text
            full_text = self._clean_text(full_text)

            logger.info(f"Extracted {len(full_text)} characters from {metadata['page_count']} pages")
            return full_text, metadata

        except Exception as e:
            logger.error(f"Error extracting text from PDF: {e}")
            raise RuntimeError(f"Failed to extract text from PDF: {str(e)}")

    def _extract_from_docx(self, file_path: str) -> Tuple[str, dict]:
        """Extract text from DOCX using python-docx."""
        text_parts = []
        metadata = {
            'file_type': 'docx',
            'page_count': 1,  # DOCX doesn't have explicit pages
            'char_count': 0,
            'extraction_method': 'python-docx'
        }

        try:
            doc = Document(file_path)

            # Extract from paragraphs
            for para in doc.paragraphs:
                if para.text.strip():
                    text_parts.append(para.text)

            # Extract from tables
            for table in doc.tables:
                for row in table.rows:
                    row_text = []
                    for cell in row.cells:
                        if cell.text.strip():
                            row_text.append(cell.text.strip())
                    if row_text:
                        text_parts.append(' | '.join(row_text))

            full_text = '\n\n'.join(text_parts)
            metadata['char_count'] = len(full_text)

            # Clean up the extracted text
            full_text = self._clean_text(full_text)

            logger.info(f"Extracted {len(full_text)} characters from DOCX")
            return full_text, metadata

        except Exception as e:
            logger.error(f"Error extracting text from DOCX: {e}")
            raise RuntimeError(f"Failed to extract text from DOCX: {str(e)}")

    def _clean_text(self, text: str) -> str:
        """Clean and normalize extracted text."""
        # Replace multiple newlines with double newline
        text = re.sub(r'\n{3,}', '\n\n', text)

        # Replace multiple spaces with single space
        text = re.sub(r' {2,}', ' ', text)

        # Remove zero-width spaces and other invisible characters
        text = text.replace('​', '').replace('﻿', '')

        # Normalize unicode
        text = text.encode('ascii', 'ignore').decode('ascii')

        # Strip leading/trailing whitespace
        text = text.strip()

        return text

    def extract_sections(self, text: str) -> dict:
        """
        Attempt to extract common resume sections from text.

        Returns:
            Dictionary with section names as keys and content as values
        """
        sections = {
            'contact': '',
            'summary': '',
            'experience': '',
            'education': '',
            'skills': '',
            'projects': '',
            'certifications': '',
            'other': ''
        }

        # Common section headers (case insensitive)
        section_patterns = {
            'contact': r'(?:contact|personal)\s*(?:info|information|details)?',
            'summary': r'(?:summary|profile|objective|about\s*me)',
            'experience': r'(?:experience|employment|work\s*history|professional\s*experience)',
            'education': r'(?:education|academic|qualifications)',
            'skills': r'(?:skills|technical\s*skills|competencies|expertise)',
            'projects': r'(?:projects|portfolio|personal\s*projects)',
            'certifications': r'(?:certifications|certificates|licenses)',
        }

        # Find section boundaries
        lines = text.split('\n')
        current_section = 'other'
        section_content = {k: [] for k in sections.keys()}

        for line in lines:
            line_lower = line.lower().strip()

            # Check if line matches a section header
            matched_section = None
            for section, pattern in section_patterns.items():
                if re.match(rf'^{pattern}[:\s]*$', line_lower, re.IGNORECASE):
                    matched_section = section
                    break

            if matched_section:
                current_section = matched_section
                continue

            if line.strip():
                section_content[current_section].append(line)

        # Join content for each section
        for section, content in section_content.items():
            sections[section] = '\n'.join(content).strip()

        return sections


def parse_resume(file_path: str) -> Tuple[str, dict]:
    """
    Convenience function to parse a resume file.

    Args:
        file_path: Path to the resume file

    Returns:
        Tuple of (extracted_text, metadata)
    """
    parser = ResumeParser()
    return parser.extract_text(file_path)