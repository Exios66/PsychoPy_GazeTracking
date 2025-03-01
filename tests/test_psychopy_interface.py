#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Test script for the PsychoPy interface.
"""

import os
import sys
import unittest
from pathlib import Path

# Add the parent directory to the path so we can import the PsychoPyInterface package
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    # Test imports from PsychoPyInterface
    from PsychoPyInterface.utils.webgazer_bridge import WebGazerBridge
    
    # Only attempt to import these if the directory exists
    if Path("PsychoPyInterface/experiments").exists():
        try:
            from PsychoPyInterface.experiments.visual_search import VisualSearchExperiment
            from PsychoPyInterface.experiments.webgazer_demo import WebGazerDemo
        except ImportError as e:
            print(f"Warning: Could not import experiment modules: {e}")
    
    class TestPsychoPyInterface(unittest.TestCase):
        """Test cases for PsychoPy interface."""
        
        def test_webgazer_bridge_init(self):
            """Test WebGazerBridge initialization."""
            bridge = WebGazerBridge(session_id="test_session")
            self.assertEqual(bridge.session_id, "test_session")
            self.assertEqual(bridge.host, "localhost")
            self.assertFalse(bridge.is_running)
        
        def test_webgazer_bridge_html(self):
            """Test WebGazerBridge HTML generation."""
            bridge = WebGazerBridge(session_id="test_session")
            html = bridge.get_client_html()
            self.assertIsInstance(html, str)
            self.assertIn("WebGazer", html)
            self.assertIn("websocket", html)
    
    if __name__ == "__main__":
        unittest.main()

except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you have activated the virtual environment and installed all dependencies.")
    print("Run: source venv/bin/activate && pip install -r requirements.txt") 