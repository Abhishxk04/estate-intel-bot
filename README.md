# Estate Intel — DarGlobal × Wasalt

A Dockerised FastAPI + retrieval-augmented chatbot that indexes publicly accessible pages from DarGlobal and Wasalt and answers using OpenRouter's free-model router. It displays source links with each response.

## Run locally

1. Copy `.env.example` to `.env` and add an OpenRouter API key (`https://openrouter.ai/keys`). The selected model defaults to `openrouter/free`.
2. Run `docker compose up --build`.
3. Open `http://localhost:8000`.

The first container start runs the crawler. It respects robots.txt, stays within the two domains, skips account/checkout/legal pages, and waits between requests. Tune `SCRAPE_MAX_PAGES` and `SCRAPE_DELAY` in `.env`. Rebuild/restart to refresh the crawl; the crawler replaces indexed rows for pages it revisits.

## Deploy

Deploy the repository to a Docker-capable host (Render, Railway, Fly.io, or a VM). Set the start command to the Dockerfile default, expose port `8000`, attach persistent storage at `/app/data`, and configure `OPENROUTER_API_KEY`, `OPENROUTER_MODEL=openrouter/free`, and `APP_URL` as environment variables. Do not commit `.env` or expose the OpenRouter key to the browser.

## API

- `GET /api/health` — health, indexed document count, model/key status.
- `GET /api/sources` — indexed page counts by source.
- `POST /api/chat` — `{ "message": "...", "history": [] }`.

## Notes and limitations

- Only publicly accessible HTML pages are indexed. Search results, dynamic listing APIs requiring login, and content blocked by robots.txt are not bypassed.
- Listings, prices, availability, and project information can change. The assistant is instructed to state when indexed sources do not establish an answer; verify current details on the official page.
- OpenRouter free models are rate-limited and model availability can change. `openrouter/free` dynamically routes to an eligible free model.
- This is an independent research demo, not affiliated with DarGlobal or Wasalt.
