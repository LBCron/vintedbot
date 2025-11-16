"""
PDF Merger Service for Bulk Shipping Labels
Merges multiple PDF shipping labels into a single file
"""
import tempfile
import httpx
from pathlib import Path
from typing import List
from fastapi.responses import FileResponse
from loguru import logger

try:
    from PyPDF2 import PdfMerger
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False
    logger.warning("PyPDF2 not installed. Install with: pip install PyPDF2")

try:
    import pikepdf
    PIKEPDF_AVAILABLE = True
except ImportError:
    PIKEPDF_AVAILABLE = False
    logger.warning("pikepdf not installed. Install with: pip install pikepdf")


class PDFMergerService:
    """Service for merging PDF files"""

    async def download_pdf(self, url: str) -> bytes:
        """Download PDF from URL"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(url)
            response.raise_for_status()
            return response.content

    async def merge_shipping_labels(self, label_urls: List[str]) -> str:
        """
        Merge multiple PDF shipping labels into one file

        Args:
            label_urls: List of PDF URLs to merge

        Returns:
            Path to merged PDF file
        """
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 required. Install with: pip install PyPDF2")

        if not label_urls:
            raise ValueError("No label URLs provided")

        logger.info(f"Merging {len(label_urls)} PDF labels")

        # Download all PDFs to temporary files
        temp_files = []
        try:
            for i, url in enumerate(label_urls):
                logger.debug(f"Downloading PDF {i+1}/{len(label_urls)}: {url}")

                # Download PDF content
                pdf_content = await self.download_pdf(url)

                # Save to temp file
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f'_label_{i}.pdf',
                    mode='wb'
                )
                temp_file.write(pdf_content)
                temp_file.close()
                temp_files.append(temp_file.name)

                logger.debug(f"Saved to: {temp_file.name}")

            # Merge PDFs
            logger.info("Merging PDFs...")
            merger = PdfMerger()

            for pdf_path in temp_files:
                merger.append(pdf_path)

            # Write merged PDF
            output_path = tempfile.mktemp(suffix='_merged_labels.pdf')
            merger.write(output_path)
            merger.close()

            logger.info(f"Merged PDF created: {output_path}")

            # Optimize with pikepdf if available
            if PIKEPDF_AVAILABLE:
                try:
                    logger.info("Optimizing PDF with pikepdf...")
                    with pikepdf.open(output_path) as pdf:
                        pdf.save(output_path, compress_streams=True, object_stream_mode=pikepdf.ObjectStreamMode.generate)
                    logger.info("PDF optimized successfully")
                except Exception as e:
                    logger.warning(f"PDF optimization failed (not critical): {e}")

            return output_path

        finally:
            # Cleanup temporary files
            for temp_file in temp_files:
                try:
                    Path(temp_file).unlink()
                except Exception as e:
                    logger.warning(f"Failed to delete temp file {temp_file}: {e}")

    async def merge_pdfs_from_bytes(self, pdf_contents: List[bytes]) -> bytes:
        """
        Merge multiple PDF byte contents into one

        Args:
            pdf_contents: List of PDF contents as bytes

        Returns:
            Merged PDF as bytes
        """
        if not PYPDF2_AVAILABLE:
            raise ImportError("PyPDF2 required. Install with: pip install PyPDF2")

        temp_files = []
        try:
            # Write contents to temp files
            for i, content in enumerate(pdf_contents):
                temp_file = tempfile.NamedTemporaryFile(
                    delete=False,
                    suffix=f'_pdf_{i}.pdf',
                    mode='wb'
                )
                temp_file.write(content)
                temp_file.close()
                temp_files.append(temp_file.name)

            # Merge
            merger = PdfMerger()
            for pdf_path in temp_files:
                merger.append(pdf_path)

            # Write to bytes
            output_path = tempfile.mktemp(suffix='_merged.pdf')
            merger.write(output_path)
            merger.close()

            # Read merged PDF
            with open(output_path, 'rb') as f:
                merged_content = f.read()

            # Cleanup output
            Path(output_path).unlink()

            return merged_content

        finally:
            # Cleanup temp files
            for temp_file in temp_files:
                try:
                    Path(temp_file).unlink()
                except:
                    pass
