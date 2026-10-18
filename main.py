import sqlite3
from datetime import datetime, timezone
from typing import Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator

# ---------- Event details ----------
EVENT_NAME = "Backend Development Workshop"
EVENT_DATE = "20 October 2026"
MAX_CAPACITY = 50

app = FastAPI(title=EVENT_NAME)


# ---------- Database ----------
def get_db():
    # isolation_level=None lets us control transactions ourselves
    conn = sqlite3.connect("students.db", isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn


def create_table():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT NOT NULL UNIQUE,
            college_department TEXT,
            registered_at TEXT NOT NULL
        )
    """)
    conn.close()


create_table()


# ---------- Input validation ----------
class StudentIn(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    college_department: Optional[str] = None

    @field_validator("name")
    @classmethod
    def clean_name(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("Name cannot be blank")
        return v

    @field_validator("email")
    @classmethod
    def lowercase_email(cls, v):
        return v.lower()


# ---------- GET /event ----------
@app.get("/event")
def event_info():
    conn = get_db()
    count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    conn.close()
    return {
        "event": EVENT_NAME,
        "date": EVENT_DATE,
        "capacity": MAX_CAPACITY,
        "seats_filled": f"{count} / {MAX_CAPACITY}",
        "seats_left": MAX_CAPACITY - count,
    }


# ---------- POST /register ----------
@app.post("/register", status_code=201)
def register(student: StudentIn):
    registered_at = datetime.now(timezone.utc).isoformat()

    conn = get_db()
    try:
        # BEGIN IMMEDIATE locks the database so two people
        # can't take the last seat at the same time
        conn.execute("BEGIN IMMEDIATE")

        count = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
        if count >= MAX_CAPACITY:
            conn.execute("ROLLBACK")
            raise HTTPException(status_code=409, detail="Event is full")

        cursor = conn.execute(
            "INSERT INTO students (name, email, college_department, registered_at) "
            "VALUES (?, ?, ?, ?)",
            (student.name, student.email, student.college_department, registered_at),
        )
        conn.execute("COMMIT")
        student_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        conn.execute("ROLLBACK")
        raise HTTPException(status_code=409, detail="This email is already registered")
    finally:
        conn.close()

    return {
        "id": student_id,
        "event": EVENT_NAME,
        "name": student.name,
        "email": student.email,
        "college_department": student.college_department,
        "registered_at": registered_at,
        "seats_filled": f"{count + 1} / {MAX_CAPACITY}",
    }


# ---------- GET /registrations ----------
@app.get("/registrations")
def view_registrations():
    conn = get_db()
    rows = conn.execute("SELECT * FROM students ORDER BY id").fetchall()
    conn.close()

    return {
        "event": EVENT_NAME,
        "date": EVENT_DATE,
        "seats_filled": f"{len(rows)} / {MAX_CAPACITY}",
        "seats_left": MAX_CAPACITY - len(rows),
        "registrations": [dict(row) for row in rows],
    }


# ---------- GET /registrations/{id} ----------
@app.get("/registrations/{registration_id}")
def view_single_registration(registration_id: int):
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM students WHERE id = ?", (registration_id,)
    ).fetchone()
    conn.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Registration not found")

    return dict(row)