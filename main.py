import os
import re
import sqlite3
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator


BASE_DIR = Path(__file__).resolve().parent
DATABASE_PATH = Path(os.getenv("STUDENT_DB_PATH", BASE_DIR / "students.db"))
SAMPLE_STUDENTS = [
    ("STU-1001", "Ava Patel", "ava.patel@example.edu", "Computer Science", 2, "Active"),
    ("STU-1002", "Noah Williams", "noah.williams@example.edu", "Business Administration", 3, "Active"),
    ("STU-1003", "Mia Chen", "mia.chen@example.edu", "Psychology", 1, "Active"),
    ("STU-1004", "Ethan Johnson", "ethan.johnson@example.edu", "Engineering", 4, "Active"),
    ("STU-1005", "Isabella Garcia", "isabella.garcia@example.edu", "Biology", 2, "Active"),
    ("STU-1006", "Liam Thompson", "liam.thompson@example.edu", "Mathematics", 3, "Inactive"),
    ("STU-1007", "Sophia Kim", "sophia.kim@example.edu", "Computer Science", 1, "Active"),
    ("STU-1008", "Oliver Brown", "oliver.brown@example.edu", "Economics", 4, "Active"),
    ("STU-1009", "Amara Okafor", "amara.okafor@example.edu", "Biology", 2, "Active"),
    ("STU-1010", "Lucas Martin", "lucas.martin@example.edu", "Engineering", 1, "Active"),
    ("STU-1011", "Priya Sharma", "priya.sharma@example.edu", "Psychology", 3, "Inactive"),
    ("STU-1012", "Daniel Wilson", "daniel.wilson@example.edu", "Business Administration", 2, "Active"),
]


class StudentInput(BaseModel):
    roll_number: str = Field(min_length=1, max_length=30)
    full_name: str = Field(min_length=2, max_length=100)
    email: str = Field(min_length=5, max_length=254)
    course: str = Field(min_length=2, max_length=100)
    year: int = Field(ge=1, le=8)
    status: Literal["Active", "Inactive"] = "Active"

    @field_validator("roll_number", "full_name", "email", "course", mode="before")
    @classmethod
    def strip_text(cls, value: object) -> object:
        return value.strip() if isinstance(value, str) else value

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", value):
            raise ValueError("Enter a valid email address")
        return value


@asynccontextmanager
async def lifespan(_: FastAPI):
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DATABASE_PATH) as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS students (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                roll_number TEXT NOT NULL UNIQUE,
                full_name TEXT NOT NULL,
                email TEXT NOT NULL,
                course TEXT NOT NULL,
                year INTEGER NOT NULL CHECK (year BETWEEN 1 AND 8),
                status TEXT NOT NULL CHECK (status IN ('Active', 'Inactive')),
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        student_count = connection.execute(
            "SELECT COUNT(*) FROM students"
        ).fetchone()[0]
        if student_count == 0:
            connection.executemany(
                """
                INSERT INTO students (roll_number, full_name, email, course, year, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                SAMPLE_STUDENTS,
            )
    yield


app = FastAPI(title="Student Record Management", lifespan=lifespan)
app.mount("/static", StaticFiles(directory=BASE_DIR / "static"), name="static")


def get_connection() -> sqlite3.Connection:
    connection = sqlite3.connect(DATABASE_PATH)
    connection.row_factory = sqlite3.Row
    return connection


@app.get("/", include_in_schema=False)
def home() -> FileResponse:
    return FileResponse(BASE_DIR / "static" / "index.html")


@app.get("/api/students")
def list_students(search: str = Query(default="", max_length=100)) -> list[dict]:
    term = f"%{search.strip()}%"
    with get_connection() as connection:
        rows = connection.execute(
            """
            SELECT id, roll_number, full_name, email, course, year, status
            FROM students
            WHERE roll_number LIKE ? OR full_name LIKE ? OR email LIKE ? OR course LIKE ?
            ORDER BY full_name COLLATE NOCASE
            """,
            (term, term, term, term),
        ).fetchall()
    return [dict(row) for row in rows]


@app.get("/api/stats")
def get_stats() -> dict[str, int]:
    with get_connection() as connection:
        row = connection.execute(
            """
            SELECT COUNT(*) AS total,
                   SUM(CASE WHEN status = 'Active' THEN 1 ELSE 0 END) AS active,
                   COUNT(DISTINCT course) AS courses
            FROM students
            """
        ).fetchone()
    return {
        "total": row["total"],
        "active": row["active"] or 0,
        "courses": row["courses"],
    }


@app.post("/api/students", status_code=201)
def create_student(student: StudentInput) -> dict:
    values = student.model_dump()
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                INSERT INTO students (roll_number, full_name, email, course, year, status)
                VALUES (:roll_number, :full_name, :email, :course, :year, :status)
                """,
                values,
            )
            row = connection.execute(
                "SELECT id, roll_number, full_name, email, course, year, status "
                "FROM students WHERE id = ?",
                (cursor.lastrowid,),
            ).fetchone()
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Roll number already exists") from error
    return dict(row)


@app.put("/api/students/{student_id}")
def update_student(student_id: int, student: StudentInput) -> dict:
    values = student.model_dump()
    try:
        with get_connection() as connection:
            cursor = connection.execute(
                """
                UPDATE students
                SET roll_number = :roll_number, full_name = :full_name,
                    email = :email, course = :course, year = :year, status = :status
                WHERE id = :id
                """,
                {**values, "id": student_id},
            )
            if cursor.rowcount == 0:
                raise HTTPException(status_code=404, detail="Student not found")
            row = connection.execute(
                "SELECT id, roll_number, full_name, email, course, year, status "
                "FROM students WHERE id = ?",
                (student_id,),
            ).fetchone()
    except sqlite3.IntegrityError as error:
        raise HTTPException(status_code=409, detail="Roll number already exists") from error
    return dict(row)


@app.delete("/api/students/{student_id}", status_code=204)
def delete_student(student_id: int) -> None:
    with get_connection() as connection:
        cursor = connection.execute("DELETE FROM students WHERE id = ?", (student_id,))
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Student not found")
