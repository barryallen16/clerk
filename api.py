import os
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from agent.orchestrator import run_agentic_workflow
from config import SQL_DB_PATH
from database.relational import init_relational_db
from database.vector import init_vector_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_relational_db()
    init_vector_db()
    yield


app = FastAPI(title="Clerk", version="0.1.0", lifespan=lifespan)
UI_DIR = Path(__file__).resolve().parent / "ui"
if UI_DIR.exists():
    app.mount("/ui", StaticFiles(directory=UI_DIR, html=True), name="ui")

API_AUTH_KEY = os.getenv("API_AUTH_KEY", "")


def verify_key(x_api_key: str = Header(default="")):
    if API_AUTH_KEY and x_api_key != API_AUTH_KEY:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")


class QueryIn(BaseModel):
    query: str
    employee_id: str | None = None


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/")
def root():
    return RedirectResponse(url="/ui")


class ResetIn(BaseModel):
    employee_id: str | None = None


@app.post("/reset")
def reset_session(
    r: ResetIn | None = None,
    x_employee_id: str = Header(default="", alias="X-Employee-ID"),
):
    emp_id = (x_employee_id or (r.employee_id if r else "") or "EMP123").strip()
    with sqlite3.connect(SQL_DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sessions (emp_id TEXT PRIMARY KEY, history TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute("DELETE FROM sessions WHERE emp_id=?", (emp_id,))
        conn.execute("UPDATE employees SET casual_balance=12, medical_balance=10 WHERE emp_id=?", (emp_id,))
        conn.commit()
    return {"status": "ok", "message": f"Session and leave balances reset for {emp_id}"}


@app.post("/query", dependencies=[Depends(verify_key)])
def query(
    q: QueryIn,
    x_employee_id: str = Header(default="", alias="X-Employee-ID"),
):
    header_id = x_employee_id.strip()
    if header_id:
        if q.employee_id and q.employee_id != header_id:
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: Cannot execute actions as '{q.employee_id}' while authenticated as '{header_id}'",
            )
        caller_id = header_id
    else:
        caller_id = q.employee_id or "EMP101"

    return run_agentic_workflow(q.query, employee_id=caller_id)
