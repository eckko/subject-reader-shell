#!/usr/bin/env python3
"""Build the publishable, encrypted site of one private book repo.

    SUBJECT_KEY=<64 hex or base64> python3 tools/book_build/build_book.py \\
        --book PATH_TO_BOOK_REPO --epub references/Book.epub \\
        [--notes-epub references/notes.epub] \\
        --template-repo eckko/encrypted-book-template --template-tag 0.1.0 \\
        --out SITE_DIR

Writes into SITE_DIR exactly the four things a subject site accepts:
index.html (loads the reader from the CDN), book.json, data/ and media/
(encrypted files only). Plain extracts and the key file live in a scratch
folder that is deleted at the end; the key is read from the environment
variable SUBJECT_KEY and never written next to the output.

Steps: unzip the book EPUB, cut it into chapters / sections / subtopics
(extract_epub.py), match ideas and questions from questions.json and encrypt
(build_site.py), add the notes EPUB (add_notes.py), write the outline
(finalize_manifest.py), then write index.html and book.json.
"""
import argparse
import json
import base64
import binascii
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TAG = re.compile(r"^\d+\.\d+\.\d+$")
ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
PAGE = """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Book</title>
<!-- generic placeholder icon, not from any book; the reader swaps in the decrypted cover -->
<link id="icon" rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 32 32'%3E%3Crect width='32' height='32' rx='7' fill='%232f6f6a'/%3E%3Cpath d='M9 8h10a4 4 0 0 1 4 4v12H13a4 4 0 0 1-4-4z' fill='none' stroke='white' stroke-width='2'/%3E%3C/svg%3E">
<link rel="stylesheet" href="https://cdn.jsdelivr.net/gh/{repo}@{tag}/style.css">
</head>
<body>
<script defer src="https://cdn.jsdelivr.net/gh/{repo}@{tag}/app.js"></script>
</body>
</html>
"""


def run(*args):
    """Run a build step; stop the build when it fails."""
    result = subprocess.run([sys.executable, *map(str, args)])
    if result.returncode != 0:
        sys.exit("build step failed: %s" % Path(str(args[0])).name)


def parse_key(text):
    """The subject key as 64 hex characters, from hex or from 32 bytes in base64."""
    text = text.strip()
    if re.fullmatch(r"[0-9a-fA-F]{64}", text):
        return text.lower()
    try:
        raw = base64.b64decode(text.replace("-", "+").replace("_", "/"), validate=True)
    except (binascii.Error, ValueError):
        return None
    return raw.hex() if len(raw) == 32 else None


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--book", type=Path, required=True)
    parser.add_argument("--epub", required=True, help="path inside the book repo")
    parser.add_argument("--notes-epub", help="path inside the book repo")
    parser.add_argument("--template-repo", default="eckko/encrypted-book-template")
    parser.add_argument("--template-tag", required=True)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args(argv)

    key = parse_key(os.environ.get("SUBJECT_KEY", ""))
    if not key:
        sys.exit("SUBJECT_KEY must be 32 bytes: 64 hex characters or base64")
    if not TAG.match(args.template_tag):
        sys.exit("the template tag must look like 0.1.0 (no \"v\", no branch)")
    book = args.book.resolve()
    out = args.out.resolve()
    if out == book or book in out.parents:
        sys.exit("--out must be outside the book repo")
    bank = json.loads((book / "questions.json").read_text(encoding="utf-8"))
    if not ID.match(bank.get("id", "")):
        sys.exit("questions.json needs a lower-case \"id\"")

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    scratch = Path(tempfile.mkdtemp(prefix="book-build-"))
    try:
        keyfile = scratch / "subject.key"
        keyfile.write_text(key)
        os.chmod(keyfile, 0o600)
        epub_dir = scratch / "epub"
        with zipfile.ZipFile(book / args.epub) as archive:
            archive.extractall(epub_dir)
        work = scratch / "work"
        work.mkdir()
        chapters = book / "book-structure" / "chapters.json"
        run(HERE / "extract_epub.py", epub_dir, chapters, work)
        run(HERE / "build_site.py", book, work, out, keyfile, epub_dir)
        if args.notes_epub:
            run(HERE / "add_notes.py", "--site", out, "--key", keyfile,
                "--notes-epub", book / args.notes_epub,
                "--report", scratch / "notes-report.json")
        run(HERE / "finalize_manifest.py", "--site", out, "--key", keyfile)
        (out / "index.html").write_text(
            PAGE.format(repo=args.template_repo, tag=args.template_tag),
            encoding="utf-8")
        (out / "book.json").write_text(
            json.dumps({"id": bank["id"], "title": bank["book"]},
                       ensure_ascii=False) + "\n", encoding="utf-8")
        # the match report is useful in the job log; it holds counts only
        report = work / "match-report.json"
        if report.exists():
            data = json.loads(report.read_text(encoding="utf-8"))
            print("unmatched ideas/questions:",
                  sum(u["unmatched_items"] for u in data["units"].values()))
    finally:
        shutil.rmtree(scratch, ignore_errors=True)

    leftovers = [p.name for p in out.iterdir()
                 if p.name not in {"index.html", "book.json", "data", "media"}]
    plain = [str(p.relative_to(out)) for part in ("data", "media")
             for p in (out / part).rglob("*") if p.is_file() and p.suffix != ".enc"]
    if leftovers or plain:
        sys.exit("refusing: unexpected output %s" % (leftovers + plain))
    print("Built %s: %d data files, %d media files" % (
        bank["id"], sum(1 for _ in (out / "data").rglob("*.enc")),
        sum(1 for _ in (out / "media").glob("*.enc"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
