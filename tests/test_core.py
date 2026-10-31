import tempfile
import unittest
from pathlib import Path
from ghostline.core import Memory
from ghostline.cli import looks_destructive

class MemoryTests(unittest.TestCase):
    def test_add_and_recent(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = Memory(Path(tmp) / "memory.jsonl")
            memory.add("user", "hello", "s1")
            memory.add("assistant", "the signal is clear", "s1")
            memory.add("user", "other session", "s2")
            self.assertEqual(len(memory.recent(session_id="s1")), 2)
            self.assertEqual(memory.recent(session_id="s1")[0]["content"], "hello")

    def test_clear(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = Memory(Path(tmp) / "memory.jsonl")
            memory.add("user", "erase me")
            memory.clear()
            self.assertEqual(memory.recent(), [])

    def test_export(self):
        with tempfile.TemporaryDirectory() as tmp:
            memory = Memory(Path(tmp) / "memory.jsonl")
            memory.add("user", "hello", "abc")
            output = memory.export_markdown(Path(tmp) / "out.md", "abc")
            self.assertIn("hello", output.read_text(encoding="utf-8"))

class SafetyTests(unittest.TestCase):
    def test_destructive_patterns(self):
        self.assertTrue(looks_destructive("rm -rf /tmp/demo"))
        self.assertTrue(looks_destructive("DROP DATABASE production"))
        self.assertFalse(looks_destructive("git status"))
        self.assertFalse(looks_destructive("python app.py"))

if __name__ == "__main__":
    unittest.main()
