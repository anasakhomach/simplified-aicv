# latex_compiler.py

import logging
import subprocess
import tempfile
import os
from typing import Dict, Any

logger = logging.getLogger(__name__)

def compile_latex_to_pdf(latex_string: str) -> Dict[str, Any]:
    """
    Compiles a LaTeX string to a PDF using pdflatex.

    Args:
        latex_string: The complete LaTeX document as a string.

    Returns:
        A dictionary with "success": True and "pdf_bytes": bytes if successful,
        or "success": False and "log": str with the error log on failure.
    """
    logger.info("Attempting to compile LaTeX string to PDF.")
    with tempfile.TemporaryDirectory() as temp_dir:
        tex_file_path = os.path.join(temp_dir, "cv.tex")
        with open(tex_file_path, "w", encoding='utf-8') as f:
            f.write(latex_string)

        # Run pdflatex twice to resolve references
        for i in range(2):
            try:
                process = subprocess.run(
                    ["pdflatex", "-interaction=nonstopmode", "-output-directory", temp_dir, tex_file_path],
                    capture_output=True,
                    text=True,
                    encoding='utf-8',
                    errors='replace'  # Handle encoding errors gracefully
                )
                if process.returncode == 0:
                    logger.info(f"pdflatex run {i+1} successful.")
                else:
                    logger.warning(f"pdflatex run {i+1} returned code {process.returncode}, but continuing...")
            except FileNotFoundError:
                logger.error("pdflatex command not found. Is a TeX distribution installed and in the system's PATH?")
                return {"success": False, "log": "pdflatex not found. Ensure LaTeX is installed."}

        pdf_file_path = os.path.join(temp_dir, "cv.pdf")
        if os.path.exists(pdf_file_path):
            with open(pdf_file_path, "rb") as f:
                pdf_bytes = f.read()
            logger.info("PDF generated successfully.")
            return {"success": True, "pdf_bytes": pdf_bytes}
        else:
            logger.error("PDF file not found after compilation.")
            # Read the log file for debugging
            log_path = os.path.join(temp_dir, "cv.log")
            if os.path.exists(log_path):
                with open(log_path, 'r', encoding='utf-8', errors='replace') as log_file:
                    log_content = log_file.read()
                logger.error(f"LaTeX log content: {log_content[-1000:]}")
                return {"success": False, "log": log_content}
            else:
                return {"success": False, "log": "Compilation failed and no log file found."}