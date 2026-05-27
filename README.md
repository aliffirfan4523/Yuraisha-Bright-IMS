# Yuraisha Bright Inventory Management System

A beginner-friendly Flask project for a Web-Based Inventory Management System for Yuraisha Bright Sdn. Bhd.

This project implements the Chapter 4 P1 requirements for a Web-Based Inventory Management System for Yuraisha Bright Sdn. Bhd. It includes authentication, inventory, usage calculation, alerts, tracking, reporting, role access, CSRF protection, and audit logging.

## Planned System Users

- Admin
- Manager

## Planned Main Modules

1. Login/Register
2. Inventory Management
3. Usage Calculation
4. Alerts and Notifications
5. Tracking
6. Reporting

## Project Structure

```text
/app
  /templates
    base.html
    index.html
    login.html
    register.html
  /static
    /css
      style.css
    /js
      script.js
  db.py
  __init__.py
  routes.py
run.py
requirements.txt
.env.example
schema.sql
README.md
```

## Setup Instructions

1. Create a virtual environment:

```bash
python -m venv venv
```

2. Activate the virtual environment.

On Windows:

```bash
venv\Scripts\activate
```

On macOS or Linux:

```bash
source venv/bin/activate
```

3. Install the required packages:

```bash
pip install -r requirements.txt
```

4. Create your environment file:

```bash
copy .env.example .env
```

On macOS or Linux:

```bash
cp .env.example .env
```

5. Update `.env` with your MySQL username and password.

6. Create the MySQL database and tables.

On Windows PowerShell:

```powershell
Get-Content schema.sql | mysql -u root -p
```

On macOS or Linux:

```bash
mysql -u root -p < schema.sql
```

7. Run the project:

```bash
python run.py
```

8. Open the app in your browser:

```text
http://127.0.0.1:5000
```

## Current Features

- Register and log in with hashed passwords
- Admin user management for roles, active status, password reset, and account deletion
- Manager/Admin inventory CRUD for boxes, plastic, and cooking oil
- Usage calculation with saved calculation history
- Automatic low-stock and delayed-delivery notifications
- Supplier delivery tracking CRUD
- Client transaction CRUD with payment status
- Inventory, stock summary, supplier, and transaction reports with CSV export
- CSRF protection for POST forms, role checks, hardened session cookie settings, validation, and audit logs

## Current Routes

- Dashboard: `http://127.0.0.1:5000/`
- Login: `http://127.0.0.1:5000/login`
- Register: `http://127.0.0.1:5000/register`
- Logout: `http://127.0.0.1:5000/logout`
- Admin Users: `http://127.0.0.1:5000/admin/users`
- Inventory: `http://127.0.0.1:5000/inventory`
- Usage: `http://127.0.0.1:5000/usage`
- Alerts: `http://127.0.0.1:5000/alerts`
- Tracking: `http://127.0.0.1:5000/tracking`
- Transactions: `http://127.0.0.1:5000/transactions`
- Reports: `http://127.0.0.1:5000/reports`

## Database Migration and Seed

For an existing local database, run:

```bash
python migrate_and_seed.py
```

If the database has no users, the script creates a default administrator:

```text
Username: admin
Password: Admin123
```

## Notes

- Use a strong `SECRET_KEY` in `.env` before deployment.
- Set `SESSION_COOKIE_SECURE=true` when serving the app over HTTPS.
