#!/usr/bin/env python3
"""
Simple launcher for the SakeMonkey Recipe Database GUI
"""

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui_app import main
    print("Starting SakeMonkey Recipe Database GUI...")
    main()
except ImportError as e:
    print(f"Error importing GUI application: {e}")
    print("Please make sure all dependencies are installed:")
    print("pip install -r requirements.txt")
except Exception as e:
    print(f"Error starting GUI: {e}")
    input("Press Enter to exit...")
