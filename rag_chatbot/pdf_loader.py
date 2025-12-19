"""
PDF Text Extraction Module
Uses PyMuPDF (fitz) for reliable text extraction from PDF files.
"""

import fitz  # PyMuPDF
from pathlib import Path
from typing import List, Dict


def extract_text_from_pdf(pdf_path: str) -> str:
    """
    Extract all text content from a PDF file.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        Extracted text as a single string
    """
    path = Path(pdf_path)
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    
    text_content = []
    
    with fitz.open(pdf_path) as doc:
        for page_num, page in enumerate(doc):
            text = page.get_text()
            if text.strip():
                text_content.append(f"[Page {page_num + 1}]\n{text}")
    
    return "\n\n".join(text_content)


def extract_text_from_multiple_pdfs(pdf_paths: List[str]) -> Dict[str, str]:
    """
    Extract text from multiple PDF files.
    
    Args:
        pdf_paths: List of paths to PDF files
        
    Returns:
        Dictionary mapping file names to extracted text
    """
    results = {}
    
    for pdf_path in pdf_paths:
        path = Path(pdf_path)
        try:
            text = extract_text_from_pdf(pdf_path)
            results[path.name] = text
            print(f"✓ Extracted text from: {path.name}")
        except Exception as e:
            print(f"✗ Error extracting from {path.name}: {e}")
            results[path.name] = ""
    
    return results


def load_all_pdfs_from_directory(directory: str) -> Dict[str, str]:
    """
    Load and extract text from all PDFs in a directory.
    
    Args:
        directory: Path to directory containing PDF files
        
    Returns:
        Dictionary mapping file names to extracted text
    """
    dir_path = Path(directory)
    if not dir_path.exists():
        raise NotADirectoryError(f"Directory not found: {directory}")
    
    # Use rglob for recursive search in subdirectories
    pdf_files = list(dir_path.rglob("*.pdf"))
    
    if not pdf_files:
        print(f"No PDF files found in {directory}")
        return {}
    
    print(f"Found {len(pdf_files)} PDF file(s)")
    return extract_text_from_multiple_pdfs([str(p) for p in pdf_files])


if __name__ == "__main__":
    # Test the PDF loader
    import sys
    
    if len(sys.argv) > 1:
        pdf_path = sys.argv[1]
        text = extract_text_from_pdf(pdf_path)
        print(f"Extracted {len(text)} characters from {pdf_path}")
        print("\n--- First 500 characters ---")
        print(text[:500])
