
@echo off
setlocal
cd app
if not exist .venv (
  py -3.11 -m venv .venv
)
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
if not exist .env (
  copy .env.example .env
  echo Created .env from template. Fill keys before production use.
)
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
