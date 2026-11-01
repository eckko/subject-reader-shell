This repo is the shell for one subject site that shows encrypted books: a hub
page (`index.html`, `subject.json`, `books.json`) plus one folder per book.
Book folders are written by `tools/add_book.py` from private book repos and
hold only `index.html`, `book.json`, `data/*.enc` and `media/*.enc`. The reader
code is never copied here: each book's `index.html` loads `app.js` and
`style.css` from https://github.com/eckko/encrypted-book-template on jsDelivr.
Never add anything else to a book folder, never add a plain book file, image
or key anywhere, never edit `books.json` by hand (run
`python3 tools/build_hub.py`), and never change a book's `id`. Use an exact
tag like `0.1.0` (no `v`, never a branch): `python3 tools/set_template_tag.py TAG`.
Run `python3 tests/test_tools.py` and `python3 tools/build_hub.py --check`
after any change. See README.md.
