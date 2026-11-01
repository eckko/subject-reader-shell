# Subject reader shell

A template for one **subject** (for example "Coding") whose books are
**encrypted**: a public GitHub Pages site with a hub page that lists the
subject's books. Each book is a folder holding only encrypted files and a
tiny `index.html`. The reader itself (the code that decrypts and shows the
book) is **not** in this repo: every book page loads it from the CDN by an
exact tag from
[`eckko/encrypted-book-template`](https://github.com/eckko/encrypted-book-template).

This is the encrypted counterpart of
[`eckko/subject-site-shell`](https://github.com/eckko/subject-site-shell).

```
<subject repo>/            public, Pages from main, folder /
  index.html               the hub: one button per book, and one key box
  subject.json             the subject's title
  books.json               written by tools/build_hub.py (do not edit)
  clean-code/              pushed by the private repo "clean-code"
    index.html             a few lines: loads app.js + style.css from the CDN
    book.json              {"id": "...", "title": "..."} (public)
    data/manifest.enc      encrypted book info and chapter list
    data/ch/*.enc          one encrypted file per chapter
    media/*.enc            encrypted figures, cover, visual summaries
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

Open the hub, open "Key: not set for this tab", paste the subject key
(64 hex characters), press Unlock, then open a book. The key is kept only for
that browser tab. You can also open a link ending in `#key=<key>`; the page
removes the key from the address straight away. Do not share links with a key.
Without a key a book page asks for one.

Today the key is typed or pasted. Fetching it from your account after sign-in
is planned in the reader template.

## Add a book

A private book repo builds the encrypted site (`index.html`, `book.json`,
`data/`, `media/`) with the template tools, then publishes it here:

1. Save the token as the secret `SUBJECT_REPO_TOKEN` in the book repo.
2. Copy `templates/publish-to-subject.yml` to
   `.github/workflows/publish-to-subject.yml` there and set `SUBJECT_REPO`.
   The book's folder name defaults to the repo's name; it must be lower-case
   letters, digits and dashes.
3. Push to `main`, or run the workflow by hand. It runs
   `tools/publish_book.sh`, which copies the book and rewrites `books.json`
   in one commit.

By hand: `python3 tools/add_book.py ../my-book --name my-book`, then commit.
To remove a book: delete its folder, run `python3 tools/build_hub.py`, commit.

## What is copied, and what is refused

Exactly four things: `index.html`, `book.json`, `data/` and `media/`.
Nothing else in the private repo is read.

`add_book.py` and the check workflow refuse a book when:

- its folder holds anything other than those four items, or `data/` or
  `media/` holds a file that is not `*.enc`, or `data/manifest.enc` is missing;
- `index.html` does not load both `app.js` and `style.css` from the CDN with
  the **same exact tag** such as `@0.1.0` (a `v` prefix, a short tag or a
  branch such as `@main` is refused, because it can change under the site);
- its `id` is missing, is not lower-case letters, digits and dashes, or is
  already used by another book in this site.

When a book is refused, nothing in the site changes.

## Change the reader version

```bash
python3 tools/set_template_tag.py 0.2.0          # every book
python3 tools/set_template_tag.py 0.2.0 --book sample
python3 tools/build_hub.py --check
```

A tag is immutable: a fix in the reader is a new tag. Optionally add a
Subresource Integrity `integrity=` hash to the two tags in a book's
`index.html`.

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
