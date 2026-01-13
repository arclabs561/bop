"""BOP integration with HOP for chat archive ingestion."""

import logging
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import HOP - prefer Rust bindings (hop_core) over Python layer (hop)
HOP_AVAILABLE = False
HOP_BACKEND = None

try:
    from hop_core import ingest_chat, quick_ingest
    HOP_AVAILABLE = True
    HOP_BACKEND = "rust"
    logger.debug("Using HOP Rust core (hop_core)")
except ImportError:
    try:
        from hop import ingest_chat, quick_ingest
        HOP_AVAILABLE = True
        HOP_BACKEND = "python"
        logger.debug("Using HOP Python layer")
    except ImportError:
        logger.warning("HOP not available. Install with: pip install hop")


class BOPIngestion:
    """BOP integration with HOP for ingesting chat archives."""

    def __init__(self):
        """Initialize BOP ingestion."""
        self.hop_available = HOP_AVAILABLE

    def ingest_archives(
        self,
        archive_path: Path,
        output_dir: Path,
        extract_metadata: bool = True,
        format: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Ingest chat archives using HOP.

        Uses hop's Python API (quick_ingest or ingest_chat).

        Args:
            archive_path: Path to archive file or directory
            output_dir: Directory to save processed content
            extract_metadata: Whether to extract metadata
            format: Optional format hint (json, markdown, text, chat)

        Returns:
            Dictionary with ingestion results

        Raises:
            ImportError: If HOP is not available
        """
        if not self.hop_available:
            raise ImportError(
                "HOP not available. Install with: pip install hop\n"
                "Or use the standalone HOP CLI: hop ingest <path>"
            )

        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)

        # Use hop's Python API
        # For chat archives, use ingest_chat; for generic, use quick_ingest
        if format == "chat" or (archive_path.is_file() and archive_path.suffix in ('.json', '.md', '.txt')):
            result = ingest_chat(
                source=archive_path,
                output_dir=output_dir,
                extractors=["dates", "entities", "topics"] if extract_metadata else [],
                output_format="markdown",
            )
        else:
            result = quick_ingest(
                source=archive_path,
                output_dir=output_dir,
            )

        return {
            "files_processed": result.get("files_processed", 0),
            "messages_extracted": result.get("items_extracted", 0),
            "metadata": result.get("metadata"),
            "output_files": result.get("output_files", []),
            "content_hash": result.get("content_hash"),  # Important for deduplication
        }

    def is_available(self) -> bool:
        """Check if HOP is available."""
        return self.hop_available

