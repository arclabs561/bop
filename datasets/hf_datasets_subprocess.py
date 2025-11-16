"""
Load HuggingFace datasets via subprocess to avoid import conflicts.

This avoids the naming conflict between local 'datasets' module and HuggingFace 'datasets' library.
"""

import subprocess
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

def _run_hf_script(script: str) -> str:
    """Run a Python script in subprocess with HuggingFace datasets available."""
    # Find site-packages from current environment
    import site
    site_packages_paths = site.getsitepackages()
    if not site_packages_paths:
        # Fallback: try common locations
        venv_path = Path(__file__).parent.parent / ".venv"
        if venv_path.exists():
            for lib_dir in venv_path.glob("lib/python*/site-packages"):
                site_packages_paths = [str(lib_dir)]
                break
    
    # Create script with site-packages path
    site_packages_str = str(site_packages_paths[0]) if site_packages_paths else ""
    full_script = f"""
import sys
import json
from pathlib import Path

# Add site-packages to path
if "{site_packages_str}":
    sys.path.insert(0, "{site_packages_str}")

{script}
"""
    
    result = subprocess.run(
        [sys.executable, "-c", full_script],
        capture_output=True,
        text=True,
        cwd=str(Path(__file__).parent.parent)
    )
    if result.returncode != 0:
        raise RuntimeError(f"Subprocess failed: {result.stderr}")
    return result.stdout


def load_fever_subprocess(split: str = "dev", max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load FEVER dataset via subprocess.
    
    Note: FEVER uses deprecated dataset scripts. We try multiple approaches:
    1. Try loading from HuggingFace Hub (may fail)
    2. Try loading from parquet files
    3. Fall back to manual download instructions
    """
    # Try loading from HuggingFace Hub directly (may work with some versions)
    script = f"""
import sys
import json

try:
    from datasets import load_dataset
    
    # Try different FEVER identifiers
    dataset_dict = None
    for identifier in ["fever/v1.0", "fever", "thomaswieland/fever"]:
        try:
            dataset_dict = load_dataset(identifier, split="{split}")
            break
        except:
            continue
    
    if dataset_dict is None:
        # Try loading from parquet
        try:
            dataset_dict = load_dataset("parquet", data_files={{
                "train": "https://huggingface.co/datasets/fever/resolve/main/train.jsonl",
                "dev": "https://huggingface.co/datasets/fever/resolve/main/dev.jsonl",
                "test": "https://huggingface.co/datasets/fever/resolve/main/test.jsonl"
            }})
            dataset = dataset_dict.get("{split}", dataset_dict.get("train", []))
        except:
            raise RuntimeError("FEVER dataset not available via HuggingFace. Please download manually from https://github.com/sheffieldnlp/fever")
    else:
        dataset = dataset_dict
    
    if {max_samples or 0}:
        dataset = dataset.select(range(min({max_samples or 0}, len(dataset))))
    
    # Convert to JSON-serializable format
    data = []
    for item in dataset:
        data.append({{
            "id": item.get("id"),
            "label": item.get("label"),
            "claim": item.get("claim"),
            "evidence": item.get("evidence", []),
        }})
    
    print(json.dumps(data))
except Exception as e:
    # Return empty list with error message
    print(json.dumps({{"error": str(e)}}))
"""
    output = _run_hf_script(script)
    result = json.loads(output)
    
    # Check if we got an error
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"Failed to load FEVER: {result['error']}. FEVER dataset scripts are deprecated. Please download manually from https://github.com/sheffieldnlp/fever or use an alternative dataset.")
    
    return result


def load_hotpotqa_subprocess(split: str = "dev", max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load HotpotQA dataset via subprocess."""
    script = f"""
from datasets import load_dataset

# Load HotpotQA
try:
    dataset_dict = load_dataset("hotpot_qa", name="fullwiki")
except:
    try:
        dataset_dict = load_dataset("hotpot_qa", name="distractor")
    except:
        raise RuntimeError("HotpotQA dataset not available")

# Handle DatasetDict vs Dataset
if hasattr(dataset_dict, "get"):
    dataset = dataset_dict.get("{split}", dataset_dict.get("dev", None))
    if dataset is None:
        # Try to get first available split
        dataset = list(dataset_dict.values())[0] if dataset_dict else None
else:
    dataset = dataset_dict

if dataset is None:
    raise RuntimeError("Could not find HotpotQA split")

# Convert to list if it's a Dataset
if hasattr(dataset, "select"):
    if {max_samples or 0}:
        dataset = dataset.select(range(min({max_samples or 0}, len(dataset))))
    items = list(dataset)
else:
    # Already a list
    items = dataset[:{max_samples or 0}] if {max_samples or 0} else dataset

# Convert to JSON-serializable format
data = []
for item in items:
    data.append({{
        "id": item.get("_id"),
        "question": item.get("question"),
        "answer": item.get("answer"),
        "supporting_facts": item.get("supporting_facts", []),
        "context": item.get("context", []),
        "type": item.get("type"),
    }})

print(json.dumps(data))
"""
    output = _run_hf_script(script)
    return json.loads(output)


def load_scifact_subprocess(max_samples: Optional[int] = None) -> List[Dict[str, Any]]:
    """Load SciFact dataset via subprocess.
    
    Note: SciFact uses deprecated dataset scripts. We try alternative approaches.
    """
    script = f"""
import sys
import json

try:
    from datasets import load_dataset
    
    # Try different SciFact identifiers
    dataset_dict = None
    for identifier in ["scifact", "allenai/scifact"]:
        try:
            dataset_dict = load_dataset(identifier, name="claims")
            break
        except:
            continue
    
    if dataset_dict is None:
        raise RuntimeError("SciFact dataset not available via HuggingFace. Dataset scripts are deprecated.")
    
    # Get train and test splits
    train_data = dataset_dict.get("train", [])
    test_data = dataset_dict.get("test", [])
    
    # Convert to lists if they're Dataset objects
    if hasattr(train_data, "__iter__") and not isinstance(train_data, (list, tuple)):
        train_data = list(train_data)
    if hasattr(test_data, "__iter__") and not isinstance(test_data, (list, tuple)):
        test_data = list(test_data)
    
    all_data = list(train_data) + list(test_data)
    
    if {max_samples or 0}:
        all_data = all_data[:{max_samples or 0}]
    
    # Convert to JSON-serializable format
    data = []
    for item in all_data:
        data.append({{
            "claim": item.get("claim"),
            "evidence": item.get("evidence", []),
            "label": item.get("label"),
            "cited_doc_ids": item.get("cited_doc_ids", []),
        }})
    
    print(json.dumps(data))
except Exception as e:
    # Return error message
    print(json.dumps({{"error": str(e)}}))
"""
    output = _run_hf_script(script)
    result = json.loads(output)
    
    # Check if we got an error
    if isinstance(result, dict) and "error" in result:
        raise RuntimeError(f"Failed to load SciFact: {result['error']}. SciFact dataset scripts are deprecated. Please use an alternative dataset or download manually.")
    
    return result

