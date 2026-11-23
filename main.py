import argparse
import sqlite3

from agent.orchestrator import run_agentic_workflow
from config import SQL_DB_PATH
from database.relational import init_relational_db
from database.vector import init_vector_db


def setup():
    print("Initializing Clerk local databases...")
    init_relational_db()
    init_vector_db()
    print("Clerk ready.\n")


def _reset_demo_state(employee_id: str):
    """Ensure --demo starts with fresh session history and baseline leave balances."""
    with sqlite3.connect(SQL_DB_PATH) as conn:
        conn.execute(
            "CREATE TABLE IF NOT EXISTS sessions (emp_id TEXT PRIMARY KEY, history TEXT NOT NULL, updated_at TEXT DEFAULT CURRENT_TIMESTAMP)"
        )
        conn.execute("DELETE FROM sessions WHERE emp_id=?", (employee_id,))
        conn.execute("UPDATE employees SET casual_balance=12, medical_balance=10 WHERE emp_id=?", (employee_id,))
        conn.commit()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--employee-id", default="EMP123")
    parser.add_argument("query", nargs="*")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args()
    setup()
    if args.demo:
        _reset_demo_state(args.employee_id)
        for q in [
            "Do I need a doctor's note for 3 days sick leave?",
            "Deduct 2 casual leave days starting 2026-06-10",
        ]:
            print(f"> Query: {q}")
            res = run_agentic_workflow(q, employee_id=args.employee_id)
            print(f"Tools called: {res.get('tools')}")
            print(f"Answer: {res.get('answer')}\n")
        return
    if args.query:
        res = run_agentic_workflow(" ".join(args.query), employee_id=args.employee_id)
        print(f"Tools called: {res.get('tools')}")
        print(f"Answer: {res.get('answer')}")
        return
    print("Interactive mode. Type 'exit' to quit.")
    while True:
        q = input("> ").strip()
        if not q or q.lower() in {"exit", "quit"}:
            break
        res = run_agentic_workflow(q, employee_id=args.employee_id)
        print(f"\n{res.get('answer')}\n")

if __name__ == "__main__":
    main()