# Event Registration Backend

A simple backend for registering students to an event and letting organizers view the registrations.

**Event:** Backend Development Workshop
**Date:** 20 October 2026
**Capacity:** 50 participants

Built with **Python**, **FastAPI** and **SQLite**.

---

## Features

- Students can register with name, email and an optional college/department
- The registration time is recorded automatically (UTC)
- Organizers can view all registrations, or a single registration by ID
- Registration closes automatically once 50 seats are filled ("Event is full")
- The same email cannot register twice (emails are not case-sensitive)
- Blank names and invalid emails are rejected
- Interactive API documentation is generated automatically

---

## Project Structure

```
student-api/
├── main.py             # the whole API
├── requirements.txt    # Python packages needed
├── .gitignore
└── README.md
```

`students.db` (the SQLite database) is created automatically the first time the server starts.

---

## Setup and Run

You need **Python 3.10 or higher**.

**1. Clone the repository and go into the folder**

```bash
git clone https://github.com/Murshidha10/event-registration-backend.git
cd event-registration-backend
```

**2. Create and activate a virtual environment**

Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

Mac / Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```

**3. Install the packages**

```bash
pip install -r requirements.txt
```

**4. Start the server**

```bash
uvicorn main:app
```

The API runs at `http://127.0.0.1:8000`.

**5. Open the interactive docs**

Go to `http://127.0.0.1:8000/docs` to try every endpoint from the browser.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/event` | Event details and seats left |
| POST | `/register` | Register a student |
| GET | `/registrations` | View all registrations (for organizers) |
| GET | `/registrations/{id}` | View a single registration |

### POST /register

Request body:

```json
{
  "name": "Priya Sharma",
  "email": "priya@example.com",
  "college_department": "Computer Science"
}
```

`college_department` is optional.

Response (`201 Created`):

```json
{
  "id": 1,
  "event": "Backend Development Workshop",
  "name": "Priya Sharma",
  "email": "priya@example.com",
  "college_department": "Computer Science",
  "registered_at": "2026-10-18T10:30:00.123456+00:00",
  "seats_filled": "1 / 50"
}
```

### GET /registrations

```json
{
  "event": "Backend Development Workshop",
  "date": "20 October 2026",
  "seats_filled": "1 / 50",
  "seats_left": 49,
  "registrations": [
    {
      "id": 1,
      "name": "Priya Sharma",
      "email": "priya@example.com",
      "college_department": "Computer Science",
      "registered_at": "2026-10-18T10:30:00.123456+00:00"
    }
  ]
}
```

### GET /registrations/{id}

Returns one registration, for example `GET /registrations/1`.

### GET /event

```json
{
  "event": "Backend Development Workshop",
  "date": "20 October 2026",
  "capacity": 50,
  "seats_filled": "1 / 50",
  "seats_left": 49
}
```

---

## Response Codes

| Situation | Status | Response |
|---|---|---|
| Successful registration | `201` | Registration details |
| Duplicate registration | `409` | `"This email is already registered"` |
| Event capacity reached | `409` | `"Event is full"` |
| Invalid or missing information | `422` | Details of the invalid field |
| Registration not found | `404` | `"Registration not found"` |

---

## Design Decisions

**Why FastAPI?**
It is simple to learn, validates incoming data automatically, and generates interactive documentation at `/docs`, which makes the API easy to test without a frontend.

**Why SQLite?**
It needs no installation or separate server. The database is a single file, which keeps the project easy to run for anyone who clones it. For a much larger system, I would move to PostgreSQL.

**How is the capacity limit enforced?**
Before saving a registration, the API counts the existing registrations. If the count has reached 50, the request is rejected with "Event is full". The count and the insert happen inside one database transaction (`BEGIN IMMEDIATE`), which locks the database. This prevents two people registering at the same moment from both taking the last seat.

**How are duplicates prevented?**
Emails are converted to lowercase before saving, so `Priya@example.com` and `priya@example.com` are treated as the same person. The database also has a `UNIQUE` rule on the email column, so duplicates are blocked even if the check in the code were bypassed.

**How is input validated?**
Pydantic models check every request. The email must be valid, the name is required, trimmed, and cannot be blank, and `college_department` is optional.

**Why parameterized SQL queries?**
All queries use `?` placeholders instead of putting user input into the SQL text. This protects against SQL injection.

---

## Testing the Capacity Limit

To avoid registering 50 students by hand:

1. Stop the server and change `MAX_CAPACITY = 50` to `MAX_CAPACITY = 2` in `main.py`.
2. Delete `students.db` and start the server again.
3. Register 3 students with different emails. The third one is rejected with `409` and `"Event is full"`.
4. Change `MAX_CAPACITY` back to `50`.

---

## Possible Improvements

- Block registrations after the event date
- Add an organizer login so only organizers can view registrations
- Add a cancel-registration endpoint
- Add automated tests
- Move to PostgreSQL for a larger deployment
