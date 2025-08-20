#!/usr/bin/env python3
"""
Test suite for the AI agent and generated parsers
"""

import pytest
import pandas as pd
import os
import sys
from pathlib import Path

def test_icici_parser_exists():
    """Test that ICICI parser was generated"""
    parser_path = "custom_parsers/icici_parser.py"
    assert os.path.exists(parser_path), f"Parser not found at {parser_path}"

def test_icici_parser_function():
    """Test that parser has correct function signature"""
    sys.path.insert(0, "custom_parsers")
    
    try:
        import icici_parser
        assert hasattr(icici_parser, 'parse'), "Parser missing parse() function"
        
        # Test with sample PDF - try multiple possible paths
        possible_pdf_paths = [
            "data/icici/icici_sample.pdf",
            "data/icici/icici sample.pdf",
            "ai-agent-challenge-main/data/icici/icici sample.pdf"
        ]
        
        pdf_path = None
        for path in possible_pdf_paths:
            if os.path.exists(path):
                pdf_path = path
                break
        
        if pdf_path:
            result = icici_parser.parse(pdf_path)
            assert isinstance(result, pd.DataFrame), "parse() must return DataFrame"
            
            # Check required columns
            expected_columns = ['Date', 'Description', 'Debit Amt', 'Credit Amt', 'Balance']
            assert list(result.columns) == expected_columns, f"Columns mismatch: {list(result.columns)}"
        else:
            pytest.skip("No ICICI sample PDF found")
            
    except ImportError as e:
        pytest.fail(f"Failed to import parser: {e}")

def test_csv_format_match():
    """Test that parser output matches expected CSV format"""
    if not os.path.exists("custom_parsers/icici_parser.py"):
        pytest.skip("Parser not generated yet")
        
    sys.path.insert(0, "custom_parsers")
    import icici_parser
    
    possible_pdf_paths = [
        "data/icici/icici_sample.pdf", 
        "data/icici/icici sample.pdf",
        "ai-agent-challenge-main/data/icici/icici sample.pdf"
    ]
    csv_path = "data/icici/result.csv"
    
    pdf_path = None
    for path in possible_pdf_paths:
        if os.path.exists(path):
            pdf_path = path
            break
    
    if pdf_path and os.path.exists(csv_path):
        result_df = icici_parser.parse(pdf_path)
        expected_df = pd.read_csv(csv_path)
        
        # Structure validation
        assert result_df.shape[1] == expected_df.shape[1], "Column count mismatch"
        assert list(result_df.columns) == list(expected_df.columns), "Column names mismatch"
    else:
        pytest.skip("Required files not found")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
