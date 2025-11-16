"""
Direct loader for HuggingFace datasets to avoid conflict with local datasets module.

Uses lazy loading with direct file import to avoid module name conflicts.
"""

import sys
import importlib.util
from pathlib import Path
from typing import Optional, Callable

_hf_load_dataset: Optional[Callable] = None
_hf_available = False
_hf_loaded = False

def _load_hf_datasets():
    """Lazy load HuggingFace datasets - only called when needed."""
    global _hf_load_dataset, _hf_available, _hf_loaded
    
    if _hf_loaded:
        return
    
    _hf_loaded = True
    
    # Find site-packages path
    site_packages_path = None
    for path in sys.path:
        if 'site-packages' in path or 'dist-packages' in path:
            site_packages_path = path
            break
    
    if not site_packages_path:
        return
    
    try:
        # Load directly from file to avoid name conflicts
        datasets_init = Path(site_packages_path) / "datasets" / "__init__.py"
        if not datasets_init.exists():
            return
        
        spec = importlib.util.spec_from_file_location(
            "huggingface_datasets_package",
            datasets_init
        )
        if not spec or not spec.loader:
            return
        
        # Need to set up the package structure for relative imports
        # Add parent directory to path temporarily
        parent_dir = str(datasets_init.parent)
        original_path = sys.path.copy()
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        
        # Load the module
        hf_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(hf_module)
        
        # Verify it's HuggingFace by checking file location
        if hasattr(hf_module, "__file__") and "site-packages" in hf_module.__file__:
            if hasattr(hf_module, "load_dataset"):
                _hf_load_dataset = hf_module.load_dataset
                _hf_available = True
        
        # Restore path
        sys.path[:] = original_path
        
    except Exception as e:
        import logging
        logging.debug(f"HuggingFace datasets import failed: {e}", exc_info=True)

def get_hf_load_dataset():
    """Get HuggingFace load_dataset function (lazy loaded)."""
    _load_hf_datasets()
    return _hf_load_dataset

def is_hf_available():
    """Check if HuggingFace datasets is available (lazy loaded)."""
    _load_hf_datasets()
    return _hf_available
