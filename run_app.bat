
@echo off
setlocal
if not exist .venv (
  py -3.11 -m venv .venv
)
call .venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
