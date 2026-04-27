# Battle Wiki Ingest Protocol

Ingest is the path from source material to reviewed doctrine.

## Steps

1. Create or update a safe raw note under `wiki/raw/`.
2. Mark source class and sensitivity.
3. Extract doctrine claims, not exact fact tables.
4. Link A-layer references when exact facts are involved.
5. Draft or update a page under `wiki/pages/`.
6. Assign confidence.
7. Run lint.
8. Request PM review for claims that will affect default synthesis.

## Source Safety

Do not place these in `wiki/raw/`:

- secrets
- cookies
- session material
- private raw chat logs
- copyrighted full-text dumps
- large raw scrape captures

Store only reviewed summaries, links, source metadata, and PM-approved notes.
