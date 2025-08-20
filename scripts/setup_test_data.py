#!/usr/bin/env python3
"""
Setup script to prepare test data structure
"""

import os
import shutil
from pathlib import Path

def setup_data_structure():
    """Create proper data directory structure"""
    
    # Create directories
    os.makedirs("data/icici", exist_ok=True)
    os.makedirs("custom_parsers", exist_ok=True)
    
    # Move files if they exist in wrong location
    old_paths = [
        "ai-agent-challenge-main/data/icici/icici sample.pdf",
        "data/icici/result.csv"
    ]
    
    new_paths = [
        "data/icici/icici_sample.pdf",
        "data/icici/result.csv"
    ]
    
    for old_path, new_path in zip(old_paths, new_paths):
        if os.path.exists(old_path) and not os.path.exists(new_path):
            print(f"Moving {old_path} -> {new_path}")
            os.makedirs(os.path.dirname(new_path), exist_ok=True)
            shutil.copy2(old_path, new_path)
    
    print("Data structure setup complete")

if __name__ == "__main__":
    setup_data_structure()
