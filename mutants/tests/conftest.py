"""Pytest configuration and fixtures"""
import sys
import os

# Add the project root to the path so imports work correctly
# This handles both normal test runs and mutmut runs
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if root not in sys.path:
    sys.path.insert(0, root)

