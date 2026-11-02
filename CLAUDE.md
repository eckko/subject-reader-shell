This repo is the shell for one subject site that shows encrypted books: a hub
page (`index.html`, `subject.json`, `books.json`) plus one folder per book.
Book folders are written by the publish workflow of a private book repo, with
the tools of https://github.com/eckko/recall-quiz-site-template (`tools/site/`)
at an exact tag, and hold only `index.html`, `read.html`, `quiz.html`,
`book.json`, `data/`, `media/` and `quiz/` (all `*.enc`). No tools or reader
code live here: every page loads `js/unlock.js` and the rest from that template
on jsDelivr. Never add anything else to a book folder, never add a plain book
file, image or key anywhere, never edit `books.json` by hand (the template's
`tools/site/build_hub.py` writes it), and never change a book's `id`. Tags are
exact like `3.1.0` (no `v`, never a branch); keep `subject.json`'s
`templateTag` in step. See README.md.

The hub `index.html` is only a fixed loader: it loads the UI (`js/hub.js`,
`css/hub.css`, icons) from https://github.com/eckko/subject-site-template on
jsDelivr at the version in `subject.json`'s `uiVersion` (`"1"` = newest 1.x.x).
Never put hub UI code, styles or icons in this repo; change them in that repo.
A new major version is adopted by hand by editing `uiVersion`.
