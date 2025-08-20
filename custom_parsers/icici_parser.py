```
import os
import re
import pdfplumber
import pandas as pd
from datetime import datetime

def parse(pdf_path: str) -> pd.DataFrame:
    """
    Parse ICICI bank statement PDF and return a pandas DataFrame.

    Args:
    pdf_path (str): Path to the ICICI bank statement PDF.

    Returns:
    pd.DataFrame: A pandas DataFrame with the parsed data.
    """
    try:
        # Open the PDF file
        with pdfplumber.open(pdf_path) as pdf:
            # Extract the text from the PDF
            text = ''
            for page in pdf.pages:
                text += page.extract_text()
        
        # Clean the text
        text = re.sub(r'\s+', ' ', text)
        text = re.sub(r'\n', ' ', text)
        text = text.strip()
        
        # Split the text into lines
        lines = text.split('\n')
        
        # Initialize the data dictionary
        data = {'Date': [], 'Description': [], 'Debit Amt': [], 'Credit Amt': [], 'Balance': []}
        
        # Iterate through the lines
        for line in lines:
            # Check if the line contains a date
            if re.match(r'\d{2}-\d{2}-\d{4}', line):
                # Extract the date
                date = datetime.strptime(line, '%d-%m-%Y').date()
                data['Date'].append(date)
            # Check if the line contains a description
            elif re.match(r'.*\d{2,3}.*', line):
                # Extract the description
                description = line
                data['Description'].append(description)
            # Check if the line contains an amount
            elif re.match(r'\d{1,3}(,\d{3})*\.?\d{0,2}', line):
                # Extract the amount
                amount = float(line.replace(',', ''))
                if re.match(r'^\d+\.?\d{0,2}$', line):
                    data['Debit Amt'].append(amount)
                elif re.match(r'^\d{1,3}(,\d{3})*\.?\d{0,2}$', line):
                    data['Credit Amt'].append(amount)
        
        # Convert the data dictionary to a pandas DataFrame
        df = pd.DataFrame(data)
        
        # Calculate the balance
        df['Balance'] = df['Credit Amt'].cumsum()
        
        return df
    
    except Exception as e:
        print(f"Error: {e}")
        return None
```