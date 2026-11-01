# Subject reader shell

A template for one **subject** (for example "Coding") whose books are
**encrypted**: a public GitHub Pages site with a hub page that lists the
subject's books. Each book is a folder holding only encrypted files and a few
tiny pages. The code that decrypts and shows a book (the reader and the quiz)
is **not** in this repo: every book page loads it from the CDN by an exact tag
from [`eckko/recall-quiz-site-template`](https://github.com/eckko/recall-quiz-site-template)
(3.0.0 and later). Each book card on the hub has two buttons, **Read book**
and **Test only**, greyed out when the book has no such view.

This is the encrypted counterpart of
[`eckko/subject-site-shell`](https://github.com/eckko/subject-site-shell).

```
<subject repo>/            public, Pages from main, folder /
  index.html               the hub: a card per book with Read book / Test only
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
  tools/  tests/  templates/
```

Nothing readable from a book is ever stored here: only ciphertext. The key
is **never** stored in any repo. One key opens every book of the subject.

## Start a new subject

1. **Use this template → Create a new repository** (public).
2. Edit `subject.json`: `{ "title": "Coding" }`. Delete `sample/` and run
   `python3 tools/build_hub.py`.
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

A private book repo builds the encrypted book folder with the build tools of
the quiz template (`tools/book_build/` in `recall-quiz-site-template`, at the
same tag the pages load) and publishes it here:

1. Save the token as the secret `READER_SUBJECT_REPO_TOKEN` and the subject key
   as `SUBJECT_KEY` in the book repo.
2. Copy `templates/publish-encrypted-book.yml` from the quiz template to
   `.github/workflows/` there and set the values at the top. The book's
   folder name defaults to the repo's name (lower-case letters, digits, dashes).
3. Push to `main`, or run the workflow by hand. It runs
   `tools/publish_book.sh`, which copies the book and rewrites `books.json`
   in one commit.

By hand: `python3 tools/add_book.py ../my-built-book --name my-book`, then
commit. To remove a book: delete its folder, run `python3 tools/build_hub.py`,
commit.

## What is copied, and what is refused

Exactly these items (those that exist): `index.html`, `read.html`,
`quiz.html`, `book.json`, `data/`, `media/` and `quiz/`. Nothing else in the
private repo is read.

`add_book.py` and the check workflow refuse a book when:

- its folder holds anything else, or `data/`, `media/` or `quiz/` holds a file
  that is not `*.enc`;
- a view listed in `book.json` is missing its files (`read`: `read.html` and
  `data/manifest.enc`; `quiz`: `quiz.html` and `quiz/questions.enc`), or those
  files exist without the view being listed;
- a page does not load `js/unlock.js` from the CDN with the **same exact tag**
  such as `@3.0.0` (a `v` prefix, a short tag or a branch such as `@main` is
  refused, because it can change under the site);
- its `id` is missing, is not lower-case letters, digits and dashes, or is
  already used by another book in this site.

When a book is refused, nothing in the site changes.

## Change the template version

```bash
python3 tools/set_template_tag.py 3.1.0          # every book
python3 tools/set_template_tag.py 3.1.0 --book sample
python3 tools/build_hub.py --check
```

A tag is immutable: a fix is a new tag. The tag in a book's pages is also what
the workflow checks the build tools out at, so re-run the book's workflow after
changing the tag it uses.

## Book ids and progress

Progress is saved under the book's `id`, in the reader's browser. Every Pages
site of one account shares one address (`<user>.github.io`), so two books with
the same id would share progress, even in different subjects. The tools check
ids within this site only, so give each book an id that no other book of yours
uses. **Never change a book's id** once readers have progress.

## Checks

`python3 tests/test_tools.py` and `python3 tools/build_hub.py --check` run on
every push (`.github/workflows/check.yml`). Also run the `check-copywright`
skill on this repo before it goes public: it must show 0 HIGH.
