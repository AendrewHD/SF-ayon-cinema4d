import unittest
import sys
import os
import re

# Add client to path so we can import ayon_cinema4d
sys.path.append(os.path.join(os.getcwd(), "client"))

from unittest.mock import MagicMock
sys.modules["c4d"] = MagicMock()
sys.modules["ayon_core"] = MagicMock()
sys.modules["ayon_core.lib"] = MagicMock()
sys.modules["ayon_core.addon"] = MagicMock()
sys.modules["ayon_cinema4d.addon"] = MagicMock()
sys.modules["pyblish"] = MagicMock()
sys.modules["pyblish.api"] = MagicMock()

# Mock ayon_cinema4d.api.pipeline because it is imported in ayon_cinema4d.api.__init__
# and it imports pyblish.api
sys.modules["ayon_cinema4d.api.pipeline"] = MagicMock()

from ayon_cinema4d.api import lib

class TestSanitizeFilename(unittest.TestCase):
    def test_basic(self):
        self.assertEqual(lib.sanitize_filename("normal_file"), "normal_file")
        self.assertEqual(lib.sanitize_filename("file-name.txt"), "file-name.txt")

    def test_unsafe_chars(self):
        self.assertEqual(lib.sanitize_filename("file/path"), "file_path")
        self.assertEqual(lib.sanitize_filename("file\\path"), "file_path")
        self.assertEqual(lib.sanitize_filename(".."), "unnamed")

    def test_empty(self):
        self.assertEqual(lib.sanitize_filename(""), "unnamed")
        self.assertEqual(lib.sanitize_filename("   "), "___")

    def test_unicode(self):
        self.assertEqual(lib.sanitize_filename("café"), "caf_")

if __name__ == "__main__":
    unittest.main()
