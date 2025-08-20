#!/usr/bin/env python3
"""
AI Agent for Bank Statement PDF Parser Generation
Develops custom parsers for bank statement PDFs using LLM-powered agent loops.
"""

import os
import sys
import argparse
import json
import pandas as pd
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging
from dataclasses import dataclass
import tempfile

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

@dataclass
class AgentState:
    """Represents the current state of the agent"""
    target_bank: str
    pdf_path: str
    csv_path: str
    parser_path: str
    attempt: int = 0
    max_attempts: int = 3
    current_plan: List[str] = None
    generated_code: str = ""
    test_results: Dict = None
    errors: List[str] = None

class BankParserAgent:
    """
    AI Agent that generates custom bank statement parsers.
    
    Architecture:
    1. Plan: Analyze PDF/CSV structure and create implementation plan
    2. Generate: Write parser code based on plan
    3. Test: Run tests to validate parser output
    4. Self-fix: Debug and correct issues (up to 3 attempts)
    """
    
    def __init__(self, api_key: str = None, model: str = "llama3-8b-8192"):
        self.api_key = "api_key" or os.getenv("GROQ_API_KEY")
        self.model = model
        self.setup_llm()
        
    def setup_llm(self):
        """Initialize LLM client"""
        try:
            from groq import Groq
            if not self.api_key:
                raise ValueError("GROQ_API_KEY environment variable not set")
            self.llm = Groq(api_key=self.api_key)
            logger.info(f"Initialized {self.model} model with Groq")
        except ImportError:
            logger.error("groq not installed. Run: pip install groq")
            sys.exit(1)
        except Exception as e:
            logger.error(f"Failed to initialize LLM: {e}")
            sys.exit(1)

    def run(self, target_bank: str) -> bool:
        """Main agent loop: plan → generate → test → self-fix"""
        logger.info(f"Starting agent for {target_bank} bank parser")
        
        # Initialize state with corrected paths
        possible_pdf_paths = [
            f"data/{target_bank}/{target_bank}_sample.pdf",
            f"data/{target_bank}/{target_bank} sample.pdf",
            f"ai-agent-challenge-main/data/{target_bank}/{target_bank} sample.pdf"
        ]
        
        pdf_path = None
        for path in possible_pdf_paths:
            if os.path.exists(path):
                pdf_path = path
                break
        
        if not pdf_path:
            logger.error(f"PDF file not found in any of these locations: {possible_pdf_paths}")
            return False
            
        state = AgentState(
            target_bank=target_bank,
            pdf_path=pdf_path,
            csv_path=f"data/{target_bank}/result.csv",
            parser_path=f"custom_parsers/{target_bank}_parser.py",
            errors=[]
        )
        
        # Validate input files
        if not self._validate_inputs(state):
            return False
            
        # Create output directory
        os.makedirs("custom_parsers", exist_ok=True)
        
        # Agent loop with self-correction
        for attempt in range(state.max_attempts):
            state.attempt = attempt + 1
            logger.info(f"Attempt {state.attempt}/{state.max_attempts}")
            
            try:
                # Step 1: Plan
                if not state.current_plan:
                    state.current_plan = self._plan_phase(state)
                    logger.info("Planning completed")
                
                # Step 2: Generate code
                state.generated_code = self._generate_phase(state)
                logger.info("Code generation completed")
                
                # Step 3: Test
                state.test_results = self._test_phase(state)
                
                if state.test_results.get("success", False):
                    logger.info("Parser generated successfully!")
                    return True
                else:
                    logger.warning(f"Tests failed on attempt {state.attempt}")
                    state.errors.append(state.test_results.get("error", "Unknown test failure"))
                    
            except Exception as e:
                logger.error(f"Error in attempt {state.attempt}: {e}")
                state.errors.append(str(e))
        
        logger.error("Failed to generate working parser after all attempts")
        return False
    
    def _validate_inputs(self, state: AgentState) -> bool:
        """Validate that required input files exist"""
        if not os.path.exists(state.pdf_path):
            logger.error(f"PDF file not found: {state.pdf_path}")
            return False
        if not os.path.exists(state.csv_path):
            logger.error(f"CSV file not found: {state.csv_path}")
            return False
        return True
    
    def _plan_phase(self, state: AgentState) -> List[str]:
        """Analyze inputs and create implementation plan"""
        logger.info("Planning phase: Analyzing PDF and CSV structure...")
        
        # Read CSV to understand expected output format
        try:
            df = pd.read_csv(state.csv_path)
            csv_info = {
                "columns": df.columns.tolist(),
                "shape": df.shape,
                "sample_rows": df.head(3).to_dict('records'),
                "data_types": df.dtypes.to_dict()
            }
        except Exception as e:
            logger.error(f"Failed to read CSV: {e}")
            raise
        
        prompt = f"""
        You are an expert Python developer creating a bank statement PDF parser.
        
        Target Bank: {state.target_bank.upper()}
        Expected CSV Output Format: {json.dumps(csv_info, indent=2, default=str)}
        
        Create a detailed implementation plan for parsing this bank's PDF statements.
        The plan should include:
        1. PDF text extraction approach
        2. Data cleaning and preprocessing steps  
        3. Pattern matching for transactions
        4. Data structure conversion to match CSV format
        5. Error handling strategies
        
        Return a JSON list of implementation steps.
        """
        
        try:
            response = self.llm.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1
            )
            plan_text = response.choices[0].message.content.strip()
            
            # Extract JSON from response
            if "\`\`\`json" in plan_text:
                plan_text = plan_text.split("\`\`\`json")[1].split("\`\`\`")[0]
            elif "[" in plan_text:
                start = plan_text.find("[")
                end = plan_text.rfind("]") + 1
                plan_text = plan_text[start:end]
            
            plan = json.loads(plan_text)
            logger.info(f"Generated plan with {len(plan)} steps")
            return plan
            
        except Exception as e:
            logger.error(f"Planning failed: {e}")
            # Fallback plan
            return [
                "Extract text from PDF using PyPDF2 or pdfplumber",
                "Clean and preprocess extracted text",
                "Identify transaction patterns using regex",
                "Parse dates, descriptions, and amounts",
                "Convert to pandas DataFrame with required columns",
                "Handle edge cases and validation"
            ]
    
    def _generate_phase(self, state: AgentState) -> str:
        """Generate parser code based on plan"""
        logger.info("⚡ Generation phase: Writing parser code...")
        
        # Read CSV for reference
        df = pd.read_csv(state.csv_path)
        csv_sample = df.head(5).to_string()
        
        previous_errors = "\n".join(state.errors) if state.errors else "None"
        
        prompt = f"""
        Generate a complete Python parser for {state.target_bank.upper()} bank statements.
        
        Requirements:
        - File: custom_parsers/{state.target_bank}_parser.py
        - Function: parse(pdf_path: str) -> pd.DataFrame
        - Output must match this CSV format exactly:
        
        {csv_sample}
        
        Implementation Plan:
        {json.dumps(state.current_plan, indent=2)}
        
        Previous Errors to Fix:
        {previous_errors}
        
        Generate COMPLETE, WORKING Python code with:
        1. All necessary imports
        2. Robust error handling
        3. Clear documentation
        4. The exact parse() function signature
        5. Data validation and cleaning
        
        Use libraries: pandas, PyPDF2 or pdfplumber, re, datetime
        
        Return ONLY the Python code, no explanations.
        """
        
        try:
            response = self.llm.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model=self.model,
                temperature=0.1
            )
            code = response.choices[0].message.content.strip()
            
            # Clean up code formatting - handle both \`\`\`python and \`\`\` blocks
            if "\`\`\`python" in code:
                code = code.split("\`\`\`python")[1].split("\`\`\`")[0]
            elif "\`\`\`" in code:
                # Find first \`\`\` and last \`\`\` to extract code block
                parts = code.split("\`\`\`")
                if len(parts) >= 3:
                    code = parts[1]
            
            # Remove any remaining markdown artifacts
            code = code.strip()
            
            # Ensure code starts with proper Python (not markdown)
            if code.startswith("\`\`\`"):
                # Remove any remaining markdown
                lines = code.split('\n')
                clean_lines = []
                in_code_block = False
                for line in lines:
                    if line.strip().startswith("\`\`\`"):
                        in_code_block = not in_code_block
                        continue
                    if in_code_block or not line.strip().startswith("\`\`\`"):
                        clean_lines.append(line)
                code = '\n'.join(clean_lines)
            
            # Write code to file
            with open(state.parser_path, 'w') as f:
                f.write(code)
            
            logger.info(f"Generated parser code ({len(code)} chars)")
            return code
            
        except Exception as e:
            logger.error(f"Code generation failed: {e}")
            raise
    
    def _test_phase(self, state: AgentState) -> Dict:
        """Test the generated parser"""
        logger.info("Testing phase: Validating parser output...")
        
        try:
            # Import the generated parser
            sys.path.insert(0, "custom_parsers")
            module_name = f"{state.target_bank}_parser"
            
            # Remove from cache if exists
            if module_name in sys.modules:
                del sys.modules[module_name]
            
            parser_module = __import__(module_name)
            
            # Test the parse function
            result_df = parser_module.parse(state.pdf_path)
            expected_df = pd.read_csv(state.csv_path)
            
            # Validate structure
            if not isinstance(result_df, pd.DataFrame):
                return {"success": False, "error": "Parser did not return a DataFrame"}
            
            if list(result_df.columns) != list(expected_df.columns):
                return {
                    "success": False, 
                    "error": f"Column mismatch. Expected: {list(expected_df.columns)}, Got: {list(result_df.columns)}"
                }
            
            # Check if DataFrames have reasonable content
            if len(result_df) == 0:
                return {"success": False, "error": "Parser returned empty DataFrame"}
                
            # Check if we have some data in the expected format
            if result_df.shape[1] == expected_df.shape[1]:
                # Validate data types are reasonable
                try:
                    # Try to convert date column if it exists
                    if 'Date' in result_df.columns:
                        pd.to_datetime(result_df['Date'].iloc[0])
                    
                    # Check if numeric columns have reasonable values
                    numeric_cols = ['Debit Amt', 'Credit Amt', 'Balance']
                    for col in numeric_cols:
                        if col in result_df.columns:
                            # Try to convert to numeric, allowing for some formatting issues
                            pd.to_numeric(result_df[col].fillna(0), errors='coerce')
                    
                    return {
                        "success": True, 
                        "message": f"Parser working correctly. Generated {len(result_df)} transactions."
                    }
                except Exception as validation_error:
                    return {
                        "success": False,
                        "error": f"Data validation failed: {validation_error}"
                    }
            else:
                return {
                    "success": False,
                    "error": f"DataFrame shape mismatch. Expected: {expected_df.shape}, Got: {result_df.shape}"
                }
            
        except ImportError as e:
            return {"success": False, "error": f"Failed to import parser: {e}"}
        except Exception as e:
            return {"success": False, "error": f"Parser execution failed: {e}"}

def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(description="AI Agent for Bank Statement PDF Parser Generation")
    parser.add_argument("--target", required=True, help="Target bank name (e.g., icici)")
    parser.add_argument("--api-key", help="Groq API key (or set GROQ_API_KEY env var)")
    parser.add_argument("--model", default="llama3-8b-8192", help="LLM model to use")
    
    args = parser.parse_args()
    
    # Initialize and run agent
    agent = BankParserAgent(api_key=args.api_key, model=args.model)
    success = agent.run(args.target)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
