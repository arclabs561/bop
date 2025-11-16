"""BOP integration with HOP for chat archive ingestion."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)

# Try to import HOP
try:
    from hop import Ingestor, IngestConfig, IngestResult
    HOP_AVAILABLE = True
except ImportError:
    HOP_AVAILABLE = False
    Ingestor = None
    IngestConfig = None
    IngestResult = None
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
        
        Args:
            archive_path: Path to archive file or directory
            output_dir: Directory to save processed content
            extract_metadata: Whether to extract metadata
            format: Optional format hint (json, markdown, text)
            
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
        
        # Configure HOP
        config = IngestConfig(
            source=str(archive_path),
            output_dir=str(output_dir),
            extract_metadata=extract_metadata,
            format=format,
        )
        
        # Create ingestor and process
        ingestor = Ingestor(config)
        
        if archive_path.is_file():
            result = ingestor.ingest_file(archive_path)
        elif archive_path.is_dir():
            result = ingestor.ingest_directory(archive_path)
        else:
            raise ValueError(f"Path is not a file or directory: {archive_path}")
        
        return {
            "files_processed": result.files_processed,
            "messages_extracted": result.messages_extracted,
            "metadata": result.metadata.model_dump() if result.metadata else None,
            "output_files": result.output_files,
        }
    
    def is_available(self) -> bool:
        """Check if HOP is available."""
        return self.hop_available

