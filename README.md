# Student Record Management System

A lightweight student directory with a Python FastAPI backend, SQLite persistence, and a responsive browser-based interface.

## Features

- Add, edit, and delete student records
- Search by name, roll number, email, or course
- Filter records by enrollment status
- Dashboard counts for total students, active students, and courses
- Input validation and duplicate roll-number protection
- Local SQLite database created automatically on startup
- Twelve sample student records added automatically to a new or empty database
- Windows launcher and desktop shortcut support

## Run locally

Python 3.10 or newer is recommended.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -m uvicorn main:app --reload
```

Open [http://127.0.0.1:8000](http://127.0.0.1:8000). Interactive API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

On Windows, double-click `Start Student Record Management.bat` to start the backend and open the UI. The `Student Record Management` desktop shortcut starts the app at the same address.

## Data storage

By default, records are stored in `students.db` in the project directory. Set `STUDENT_DB_PATH` to use a different SQLite file, for example:

```powershell
$env:STUDENT_DB_PATH = "C:\data\students.db"
python -m uvicorn main:app --reload
```

Sample names are only added when the database has no student records; they are not added again after you start editing the list.

## Student fields

Each record has a unique roll number, full name, email, course, year (1–8), and status (`Active` or `Inactive`).

This starter app does not include authentication. Keep it local for demos; add authentication and HTTPS before deploying student information to a shared or public environment.
