
# Edu RAG – Windows (Cloud Mode)

**Requires**: OpenAI, Pinecone, AWS S3 keys in `.env`.

## Quick Start
1) Double-click `run_app.bat` (creates venv, installs dependencies).
2) Fill `.env` with real keys (OpenAI, Pinecone, AWS S3).
3) Run `run_app.bat` again.
4) Open http://localhost:8080/docs

## Flow
- `POST /ingest/unit` -> builds preview (chunks + image refs)
- `GET /ingest/job/{id}/preview` -> review
- `POST /ingest/job/{id}/approve` -> uploads images to S3, upserts vectors to Pinecone
- `GET /admin/unit/{unitId}/images` -> presigned URLs
- `POST /qa/query` -> subject+unit-filtered RAG answer

## Notes
- Set `USE_MATHPIX=true` and provide `MATHPIX_APP_ID/KEY` to extract LaTeX from images.
- SQLite by default; switch `DB_URL` to Postgres/MySQL if desired.
