import unittest
from main import *
string = "abcdefghijklmnopqrstuvwxyz"

class fuzzyTest(unittest.TestCase):
    def test_whole(self):
        self.assertEqual(
            fuzzy_search("abc", string),
            WHOLE_PATTERN_IN_STRING)
    def test_fuzz(self):
        self.assertEqual(
            fuzzy_search("agh", string),
            PATTERN_IN_STRING)
    def test_notfound(self):
        self.assertEqual(
            fuzzy_search("bede", string),
            PATTERN_NOT_FOUND)
    def test_notfoundwithdupe(self):
        self.assertEqual(
            fuzzy_search("qq", "qwerty"),
            PATTERN_NOT_FOUND)

class highlightTest(unittest.TestCase):
    def test_one(self):
        self.assertEqual(process_item("bede", pattern="d"),
                         "b e [BOLD]d[/BOLD] e")
    def test_two(self):
        self.assertEqual(process_item("abcba", pattern="ba"),
                         "a [BOLD]b[/BOLD] c b [BOLD]a[/BOLD]")

    def test_caps(self):
        self.assertEqual(process_item("Luakit", pattern="Lu"),
                         "[BOLD]L[/BOLD] [BOLD]u[/BOLD] a k i t")

unittest.main()
