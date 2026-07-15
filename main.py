import os
import sys
from dotenv import load_dotenv
from datetime import datetime
from print_color import print

#Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def print_header():
    """Print a nice header"""
    print("\n" + "=" * 60, color='green')
    a = "DocDacity Intelligent Document Assistant"
    print(a.upper(), color='green')
    print("=" * 60 + "\n", color='green')

def print_help():
    """Print help information"""
    print("\nAVAILABLE COMMANDS:", color='blue')
    print("  /help     - Show this help message")
    print("  /docs     - List available documents")
    print("  /quit     - Exit the assistant")
    print("\nExample queries:")
    print("  - What's the total amount in invoice INV-001?")
    print("  - Summarize all contracts")
    print("  - Calculate the sum of all invoice totals")
    print("  - Find documents with amounts over $50,000")
    print()
