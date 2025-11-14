#!/usr/bin/env python3
"""
ESAC v1 - EQ-SANS Assisting Chatbot

A PyQt5-based desktop application for creating and editing Python scripts
for EQ-SANS experiments with AI assistance.
"""

__version__ = "1.0.0"
__author__ = "ESAC Development Team"

if __name__ == "__main__":
    import sys
    import os
    sys.path.insert(0, os.path.dirname(__file__))
    from main import *