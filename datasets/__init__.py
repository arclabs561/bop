"""Dataset loading utilities for BOP evaluations."""

from pathlib import Path
import json
from typing import Dict, List, Any, Optional


def load_dataset(dataset_path: Path) -> List[Dict[str, Any]]:
    """Load a dataset from a JSON file."""
    if not dataset_path.exists():
        raise FileNotFoundError(f"Dataset not found: {dataset_path}")
    
    with open(dataset_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_all_datasets(datasets_dir: Path) -> Dict[str, List[Dict[str, Any]]]:
    """Load all datasets from a directory."""
    datasets = {}
    
    if not datasets_dir.exists():
        return datasets
    
    for dataset_file in datasets_dir.glob("*.json"):
        dataset_name = dataset_file.stem
        try:
            datasets[dataset_name] = load_dataset(dataset_file)
        except Exception as e:
            print(f"Warning: Failed to load {dataset_file}: {e}")
    
    return datasets


def get_dataset_by_domain(datasets_dir: Path, domain: str) -> List[Dict[str, Any]]:
    """Get all datasets for a specific domain."""
    all_datasets = load_all_datasets(datasets_dir)
    return [
        item for dataset_name, items in all_datasets.items()
        if dataset_name.startswith(domain)
        for item in items
    ]

