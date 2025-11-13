# GYM Management — DBMS Mini Project

This repository contains the DBMS mini project: a Gym Management System built with Flask and MySQL.

## Project Overview

- Project type: DBMS Mini Project
- Purpose: Manage gyms, members, trainers, payments and run advanced SQL queries (JOIN, NESTED, AGGREGATE) with a web UI.
- Backend: Flask (Python)
- Database: MySQL (schema & seed data in `gym_enhanced.sql`)
- Frontend: Jinja2 templates + Bootstrap + custom CSS

## Team

- Farhaan Arshad (PES2UG23AM035)
- Dhriti Rai (PES2UG23AM035)

## Repository Structure (key files)

- `app.py` — Main Flask application and routes
- `gym_enhanced.sql` — Database schema and seed data
- `requirements.txt` — Python dependencies
- `templates/` — HTML templates (members, trainers, payments, queries, audit, etc.)
- `static/css/style.css` — Global styles (dark theme)

## Features

- CRUD for Members, Trainers, Payments
- Audit logs
- Advanced queries (JOIN, nested/subquery, aggregate) exposed via UI and secured by role
- Role-based access: admin/viewer
- Dark themed UI with responsive tables

## Prerequisites

- Python 3.8+ (3.10/3.11 recommended)
- MySQL server
- pip (Python package manager)

## Setup & Run (quick)

1. Create and activate a Python virtual environment (recommended):

```bash
python3 -m venv venv
source venv/bin/activate
```

2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Create the MySQL database and import schema & seed data (adjust DB user/password as needed):

```bash
# from MySQL shell or a client
CREATE DATABASE GYM;
USE GYM;
# then import the SQL file (example using mysql CLI)
mysql -u root -p GYM < gym_enhanced.sql
```

4. Configure database connection in `app.py` (update host/user/password/database if necessary). Example in `app.py` looks for a running MySQL instance — edit credentials there if required.

5. Run the app locally:

```bash
python app.py
```

The app will typically run at http://127.0.0.1:5000 — open in your browser.

## Notes & Tips

- If you see a 403 or missing navigation link for "Advanced Queries", you may be logged in as a `viewer` role (read-only).
- The `gym_enhanced.sql` contains the schema and seed data used for testing. Re-importing it will reset data.
- `test.py` present in the repo is from a different experiment/project and is not used by the Gym web app.

## Troubleshooting

- If the server exits quickly or crashes with Exit Code 1/137, check the terminal logs, confirm MySQL is running, and verify credentials in `app.py`.
- For styling issues, clear browser cache or ensure `static/css/style.css` is being loaded.

## License & Credits

This project was created as a DBMS mini-project by the team above. Feel free to adapt for educational use.


