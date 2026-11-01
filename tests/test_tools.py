#!/usr/bin/env python3
"""Tests for the subject site tools. Run: python3 tests/test_tools.py"""

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "tools"))

import add_book  # noqa: E402
import build_hub  # noqa: E402
import set_template_tag  # noqa: E402

PAGE = ('<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/o/r@%(t)s/style.css">'
        '<script defer src="https://cdn.jsdelivr.net/gh/o/r@%(t)s/app.js"></script>')


def make_book(folder, book_id="b1", title="Book One", tag="0.1.0"):
    """Create a minimal valid book (as a private repo's output) in folder."""
    (folder / "data" / "ch").mkdir(parents=True)
    (folder / "media").mkdir()
    (folder / "index.html").write_text(PAGE % {"t": tag}, encoding="utf-8")
    (folder / "book.json").write_text(
        json.dumps({"id": book_id, "title": title}), encoding="utf-8")
    (folder / "data" / "manifest.enc").write_bytes(b"RQE1")
    (folder / "data" / "ch" / "c01.enc").write_bytes(b"RQE1")
    (folder / "media" / "f1.enc").write_bytes(b"RQE1")


class SiteCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.site = self.tmp / "site"
        self.site.mkdir()
        (self.site / "subject.json").write_text('{"title": "T"}')
        (self.site / "index.html").write_text("<html></html>")
        self.src = self.tmp / "src"
        self.src.mkdir()

    def tearDown(self):
        shutil.rmtree(self.tmp)


class AddBookTests(SiteCase):
    def test_adds_a_valid_book_and_writes_books_json(self):
        make_book(self.src)
        self.assertEqual(add_book.add_book(self.src, "b1", self.site), [])
        self.assertTrue((self.site / "b1" / "data" / "manifest.enc").is_file())
        books = json.loads((self.site / "books.json").read_text())["books"]
        self.assertEqual(books[0]["id"], "b1")
        self.assertEqual(build_hub.main(["--check", "--subject-root", str(self.site)]), 0)

    def test_only_four_items_are_copied(self):
        make_book(self.src)
        (self.src / "references").mkdir()
        (self.src / "references" / "book.epub").write_bytes(b"plain")
        (self.src / "notes.docx").write_bytes(b"plain")
        self.assertEqual(add_book.add_book(self.src, "b1", self.site), [])
        self.assertEqual({p.name for p in (self.site / "b1").iterdir()},
                         {"index.html", "book.json", "data", "media"})

    def test_refuses_a_plain_file_in_data_or_media(self):
        make_book(self.src)
        (self.src / "media" / "cover.png").write_bytes(b"plain")
        self.assertTrue(add_book.add_book(self.src, "b1", self.site))
        self.assertFalse((self.site / "b1").exists())
        (self.src / "media" / "cover.png").unlink()
        (self.src / "data" / "ch" / "c02.json").write_text("{}")
        self.assertTrue(add_book.add_book(self.src, "b1", self.site))

    def test_refuses_a_branch_a_v_prefix_or_mixed_tags(self):
        for bad in ("main", "v0.1.0", "0.1"):
            make_book(self.src / ("x" + bad), tag=bad)
            self.assertTrue(add_book.add_book(self.src / ("x" + bad), "b1", self.site), bad)
        make_book(self.src / "mix")
        (self.src / "mix" / "index.html").write_text(
            '<link href="https://cdn.jsdelivr.net/gh/o/r@0.1.0/style.css">'
            '<script src="https://cdn.jsdelivr.net/gh/o/r@0.2.0/app.js"></script>')
        self.assertTrue(add_book.add_book(self.src / "mix", "b1", self.site))

    def test_refuses_duplicate_ids_and_keeps_site_unchanged(self):
        make_book(self.src / "a", book_id="same")
        make_book(self.src / "b", book_id="same")
        self.assertEqual(add_book.add_book(self.src / "a", "a", self.site), [])
        before = (self.site / "books.json").read_text()
        self.assertTrue(add_book.add_book(self.src / "b", "b", self.site))
        self.assertEqual((self.site / "books.json").read_text(), before)
        self.assertFalse((self.site / "b").exists())

    def test_missing_manifest_is_refused(self):
        make_book(self.src)
        (self.src / "data" / "manifest.enc").unlink()
        self.assertTrue(add_book.add_book(self.src, "b1", self.site))


class HubTests(SiteCase):
    def test_stale_books_json_fails_check(self):
        make_book(self.site / "b1")
        self.assertEqual(build_hub.main(["--check", "--subject-root", str(self.site)]), 1)
        self.assertEqual(build_hub.main(["--subject-root", str(self.site)]), 0)
        self.assertEqual(build_hub.main(["--check", "--subject-root", str(self.site)]), 0)

    def test_unexpected_top_level_file_is_a_problem(self):
        (self.site / "book.epub").write_bytes(b"plain")
        _, problems = build_hub.check_site(self.site)
        self.assertTrue(any("book.epub" in p for p in problems))

    def test_extra_item_in_a_book_folder_is_a_problem(self):
        make_book(self.site / "b1")
        (self.site / "b1" / "questions.json").write_text("{}")
        _, problems = build_hub.check_site(self.site)
        self.assertTrue(any("questions.json" in p for p in problems))


class TagTests(SiteCase):
    def test_sets_the_tag_in_every_book(self):
        make_book(self.site / "a")
        make_book(self.site / "b", book_id="b2")
        self.assertEqual(set_template_tag.main(["0.3.0", "--subject-root", str(self.site)]), 0)
        for name in ("a", "b"):
            text = (self.site / name / "index.html").read_text()
            self.assertEqual(text.count("@0.3.0/"), 2)
            self.assertNotIn("@0.1.0", text)

    def test_refuses_a_branch_or_v_prefix(self):
        make_book(self.site / "a")
        for bad in ("main", "v0.3.0", "1.0"):
            self.assertEqual(set_template_tag.main([bad, "--subject-root", str(self.site)]), 1)
        self.assertIn("@0.1.0", (self.site / "a" / "index.html").read_text())


class ThisRepoTests(unittest.TestCase):
    def test_this_site_is_valid_and_hub_is_current(self):
        self.assertEqual(build_hub.main(["--check"]), 0)

    def test_no_plain_book_files_are_committed(self):
        names = [p.name for p in ROOT.rglob("*")
                 if ".git" not in p.parts and p.is_file()]
        self.assertFalse([n for n in names if n.endswith((".epub", ".pdf", ".key"))])


if __name__ == "__main__":
    unittest.main()
