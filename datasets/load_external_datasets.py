"""
Load external datasets for evaluation.

Supports:
- FEVER (fact verification)
- HotpotQA (multi-document QA)
- SciFact (scientific fact checking)
- TSVer (temporal reasoning)
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

logger = logging.getLogger(__name__)

# Import HuggingFace datasets via subprocess to avoid conflict
try:
    from .hf_datasets_subprocess import (
        load_fever_subprocess,
        load_hotpotqa_subprocess,
        load_scifact_subprocess,
    )
    DATASETS_AVAILABLE = True
except ImportError:
    DATASETS_AVAILABLE = False
    logger.warning("HuggingFace datasets subprocess loader not available")


def load_fever(split: str = "train", max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load FEVER dataset for fact verification.
    
    Args:
        split: Dataset split ("train", "dev", "test")
        max_samples: Maximum number of samples to load (None for all)
    
    Returns:
        List of claim dictionaries with 'id', 'label', 'claim', 'evidence'
    """
    if not DATASETS_AVAILABLE:
        raise ImportError("HuggingFace datasets required. Install with: pip install datasets")
    
    logger.info(f"Loading FEVER {split} split...")
    # Use subprocess to avoid import conflicts
    try:
        data = load_fever_subprocess(split=split, max_samples=max_samples)
    except Exception as e:
        logger.warning(f"Failed to load FEVER: {e}")
        return []
    
    logger.info(f"Loaded {len(data)} FEVER claims")
    return data


def load_hotpotqa(split: str = "dev", max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load HotpotQA dataset for multi-document question answering.
    
    Args:
        split: Dataset split ("train", "dev", "test")
        max_samples: Maximum number of samples to load (None for all)
    
    Returns:
        List of question dictionaries with 'question', 'answer', 'supporting_facts', 'context'
    """
    if not DATASETS_AVAILABLE:
        raise ImportError("HuggingFace datasets required. Install with: pip install datasets")
    
    logger.info(f"Loading HotpotQA {split} split...")
    # Use subprocess to avoid import conflicts
    try:
        data = load_hotpotqa_subprocess(split=split, max_samples=max_samples)
    except Exception as e:
        logger.warning(f"Failed to load HotpotQA: {e}")
        return []
    
    logger.info(f"Loaded {len(data)} HotpotQA questions")
    return data


def load_scifact(max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Load SciFact dataset for scientific fact checking.
    
    Args:
        max_samples: Maximum number of samples to load (None for all)
    
    Returns:
        List of claim dictionaries with 'claim', 'evidence', 'label'
    """
    if not DATASETS_AVAILABLE:
        raise ImportError("HuggingFace datasets required. Install with: pip install datasets")
    
    logger.info("Loading SciFact dataset...")
    # Use subprocess to avoid import conflicts
    try:
        data = load_scifact_subprocess(max_samples=max_samples)
    except Exception as e:
        logger.warning(f"Failed to load SciFact: {e}")
        return []
    
    logger.info(f"Loaded {len(data)} SciFact claims")
    return data


def load_tsver(dataset_path: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    Load TSVer dataset for temporal reasoning.
    
    Args:
        dataset_path: Path to TSVer JSON file (if None, tries to download)
    
    Returns:
        List of claim dictionaries with temporal evidence
    """
    if dataset_path is None:
        # TSVer is not on HuggingFace, would need direct download
        logger.warning("TSVer dataset not available. Please download manually from paper repository.")
        return []
    
    logger.info(f"Loading TSVer from {dataset_path}...")
    with open(dataset_path, "r") as f:
        data = json.load(f)
    
    logger.info(f"Loaded {len(data)} TSVer claims")
    return data


def get_dataset_summary() -> Dict[str, Any]:
    """Get summary of available datasets."""
    summary = {
        "datasets_available": DATASETS_AVAILABLE,
        "external_datasets": {
            "fever": {
                "description": "Fact Extraction and VERification (185,445 claims)",
                "available": DATASETS_AVAILABLE,
                "splits": ["train", "dev", "test"],
            },
            "hotpotqa": {
                "description": "Multi-hop Question Answering (113k questions)",
                "available": DATASETS_AVAILABLE,
                "splits": ["train", "dev", "test"],
            },
            "scifact": {
                "description": "Scientific Fact Checking (1,409 claims)",
                "available": DATASETS_AVAILABLE,
                "splits": ["train", "test"],
            },
            "tsver": {
                "description": "Time-Series Verification (287 claims)",
                "available": False,  # Not on HuggingFace
                "note": "Requires manual download",
            },
        },
        "internal_datasets": {
            "calibration_ground_truth": {
                "description": "Calibration scenarios with known ground truth",
                "path": "datasets/calibration_ground_truth.json",
                "available": True,
            },
            "source_credibility_ground_truth": {
                "description": "Source credibility scores with known ground truth",
                "path": "datasets/source_credibility_ground_truth.json",
                "available": True,
            },
        },
    }
    return summary

