# AI Agent Challenge - Bank Statement PDF Parser

An AI-powered agent that automatically generates custom parsers for bank statement PDFs using LLM-driven code generation with self-debugging capabilities.

## Architecture

The agent follows a **Plan → Generate → Test → Self-Fix** loop:

1. **Plan**: Analyzes PDF/CSV structure and creates implementation strategy
2. **Generate**: Writes parser code using LLM based on the plan  
3. **Test**: Validates parser output against expected CSV format
4. **Self-Fix**: Debugs and corrects issues (up to 3 attempts)

## Quick Start (5 steps)

### 1. Setup Environment
\`\`\`bash
git clone <repository>
cd ai-agent-challenge
pip install -r requirements.txt
\`\`\`

### 2. Get API Key
Get free Gemini API or Groq API key from [Google AI Studio](https://makersuite.google.com/app/apikey)

### 3. Set Environment Variable
\`\`\`bash
export GROQ_API_KEY="your-api-key-here"
\`\`\`

### 4. Run Agent
\`\`\`bash
python agent.py --target icici
\`\`\`

### 5. Test Results
\`\`\`bash
python -m pytest test_agent.py -v
\`\`\`

## Usage

### Generate ICICI Parser
\`\`\`bash
python agent.py --target icici
\`\`\`

### Generate Parser for New Bank (e.g., SBI)
\`\`\`bash
# 1. Create data directory structure
mkdir -p data/sbi

# 2. Add your SBI PDF and expected CSV
cp your_sbi_statement.pdf data/sbi/sbi_sample.pdf
cp expected_output.csv data/sbi/result.csv

# 3. Run agent
python agent.py --target sbi
\`\`\`

### Custom Model/API Key
\`\`\`bash
python agent.py --target icici --api-key YOUR_KEY --model gemini-1.5-pro
\`\`\`

## Output

The agent generates `custom_parsers/{bank}_parser.py` with:
- `parse(pdf_path: str) -> pd.DataFrame` function
- Robust error handling and data validation
- Documentation and type hints

## Agent Capabilities

- **Autonomous**: Self-debugging loops with up to 3 correction attempts
- **Adaptive**: Works with any bank by analyzing PDF/CSV patterns
- **Robust**: Comprehensive error handling and validation
- **Extensible**: Easy to add new banks without code changes

## Requirements

- Python 3.8+
- Gemini API key (free tier available)
- PDF files and expected CSV output for training

## Architecture Diagram

\`\`\`
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   Plan      │───▶│   Generate   │───▶│    Test     │
│ Analyze I/O │    │  Write Code  │    │ Validate    │
└─────────────┘    └──────────────┘    └─────────────┘
       ▲                                       │
       │            ┌─────────────┐            │
       └────────────│  Self-Fix   │◀───────────┘
                    │ Debug Loop  │
                    └─────────────┘
\`\`\`

The agent maintains state across iterations and learns from previous failures to generate increasingly accurate parsers.
