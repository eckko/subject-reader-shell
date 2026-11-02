# Subject reader shell

A template for one **subject** (for example "Coding") whose books are
**encrypted**: a public GitHub Pages site with a hub page that lists the
subject's books. Each book is a folder holding only encrypted files and a few
tiny pages. The code that decrypts and shows a book (the reader and the quiz)
is **not** in this repo: every book page loads it from the CDN by an exact tag
from [`eckko/recall-quiz-site-template`](https://github.com/eckko/recall-quiz-site-template)
(3.0.0 and later). Each book card on the hub has two buttons, **Read book**
and **Test only**, greyed out when the book has no such view.

## The hub UI (not in this repo)

`index.html` is a tiny fixed loader. It reads `uiVersion` from `subject.json`
and loads the whole hub UI (sign-in screen, shelf with covers, search, sort,
filters, cards / list / compact views, the gear and the icons) from
[`eckko/subject-site-template`](https://github.com/eckko/subject-site-template)
on jsDelivr. `"uiVersion": "1"` means the newest `1.x.x` release, so minor and
patch updates reach this site by themselves (a browser may take a while to see
one because of caching). **Subject repos hold encrypted data only; all UI
changes are made in that repo.** A new major version (breaking changes) is
adopted by hand: set `"uiVersion": "2"` in `subject.json`. Pin an exact
release (`"1.2.3"`) to stop updates.

The hub is **sign-in only**: until the reader has signed in (or pasted the
key) it shows nothing but a sign-in screen; the gear works there too. After
that it shows each book's cover (decrypted from
`<book>/media/<id>_front_cover.enc`), with search, filters, sort, views and
the gear (theme, font size, **Sign out**). Progress comes from this browser's
saved quiz progress. It starts in the Classic theme, light, at 16px.

`subject.json` can add `bookDetails` for the cards:
`{"<book id>": {"authors": ["Name"], "edition": "2nd", "year": 2018}}`.

This is the encrypted counterpart of
[`eckko/subject-site-shell`](https://github.com/eckko/subject-site-shell).

```
<subject repo>/            public, Pages from main, folder /
  index.html               the hub shell: loads the hub UI from the CDN by tag
  subject.json             the subject's title
  books.json               written by tools/build_hub.py (do not edit)
  clean-code/              pushed by the private repo "clean-code"
    index.html             the gate: unlock, then ?view=read or ?view=quiz
    read.html  quiz.html   tiny pages that start the reader / the quiz
    book.json              {"id", "title", "views"} (public)
    data/manifest.enc      the reader: encrypted book info and chapter list
    data/ch/*.enc          the reader: one encrypted file per chapter
    media/*.enc            the reader: encrypted figures, cover, summaries
    quiz/questions.enc     the quiz: all questions, same key
    quiz/media/**/*.enc    the quiz: encrypted pictures, same key
  sample/                  a tiny sample book (delete it for a real subject)
  .github/workflows/check.yml   runs the template's checks (no tools here)
```

Nothing readable from a book is ever stored here: only ciphertext. The key
is **never** stored in any repo. One key opens every book of the subject.

## Start a new subject

1. **Use this template → Create a new repository** (public).
2. Edit `subject.json`: `{ "title": "Coding", "templateTag": "3.1.0" }`
   (the tag of the quiz template whose tools check this site). Delete
   `sample/` and `books.json`'s entry for it (the check workflow or
   `python3 build_hub.py` from the template rewrites `books.json`).
3. **Settings → Pages → Deploy from a branch**, branch `main`, folder
   `/ (root)`. The hub is at `https://<user>.github.io/<repository>/`.
4. Create a fine-grained personal access token limited to this repository
   with **Contents: Read and write**.

## Open a book

On the hub press **Read book** or **Test only**. The book page asks for the key
if this tab does not have it: **Sign in with Google** (the key is read from
your account, see below) or paste it. Both views share the key for the tab.

The key lives in Firestore at `users/<your uid>/mediaKeys/subject`, field
`key` (64 hex characters or 32 bytes in base64). You create that document by
hand; the security rules let only your account read it. Add the site's domain
(for example `<user>.github.io`) under Firebase Authentication > Authorized
domains.

## Add a book

A private book repo builds the encrypted book folder and publishes it here,
both with the tools of the quiz template at one exact tag
(`tools/book_build/` and `tools/site/` in `recall-quiz-site-template`). This
repo holds no tools of its own, so it can never fall behind them.

1. Save the token as the secret `READER_SUBJECT_REPO_TOKEN` and the subject key
   as `SUBJECT_KEY` in the book repo.
2. Copy `templates/publish-encrypted-book.yml` from the quiz template to
   `.github/workflows/` there and set the values at the top. The book's
   folder name defaults to the repo's name (lower-case letters, digits, dashes).
3. Push to `main`, or run the workflow by hand. It builds the book, checks it
   and commits it here together with the rewritten `books.json`.

To remove a book: delete its folder and run the check workflow's
`build_hub.py` (or `python3 <template>/tools/site/build_hub.py`) to rewrite
`books.json`, then commit.

## What is copied, and what is refused

Exactly these items (those that exist): `index.html`, `read.html`,
`quiz.html`, `book.json`, `data/`, `media/` and `quiz/`. Nothing else in the
private repo is read.

The checks (`tools/site/build_hub.py` and `add_book.py` in the template, run
by the publish workflow and by `.github/workflows/check.yml` here) refuse a
book when:

- its folder holds anything else, or `data/`, `media/` or `quiz/` holds a file
  that is not `*.enc`;
- a view listed in `book.json` is missing its files (`read`: `read.html` and
  `data/manifest.enc`; `quiz`: `quiz.html` and `quiz/questions.enc`), or those
  files exist without the view being listed;
- a page does not load `js/unlock.js` from the CDN with the **same exact tag**
  such as `@3.1.0` (a `v` prefix, a short tag or a branch such as `@main` is
  refused, because it can change under the site);
- its `id` is missing, is not lower-case letters, digits and dashes, or is
  already used by another book in this site.

When a book is refused, nothing in the site changes.

## Change the template version

Re-run each book's publish workflow with the new `TEMPLATE_TAG`: the pages,
the build and the publish tools all move to that tag together. Then set
`templateTag` in `subject.json` to the same tag. A tag is immutable: a fix is a
new tag.

## Book ids and progress

Progress is saved under the book's `id`, in the reader's browser. Every Pages
site of one account shares one address (`<user>.github.io`), so two books with
the same id would share progress, even in different subjects. The tools check
ids within this site only, so give each book an id that no other book of yours
uses. **Never change a book's id** once readers have progress.

## Checks

`.github/workflows/check.yml` runs the template's `build_hub.py --check` on
every push. Also run the `check-copywright` skill on this repo before it goes
public: it must show 0 HIGH.
