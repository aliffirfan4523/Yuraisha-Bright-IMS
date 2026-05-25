# Yuraisha Bright Inventory Management System

A beginner-friendly Flask project for a Web-Based Inventory Management System for Yuraisha Bright Sdn. Bhd.

This project now includes a basic Login/Register module connected to the `users` table in MySQL. Inventory, usage calculation, alerts, tracking, and reporting pages will be added later.

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

- Register an Admin or Manager account
- Save users to the `users` table using `full_name`, `username`, `email`, `password_hash`, and `role`
- Store passwords safely using password hashing
- Login with username/email and password
- Use Flask sessions to remember the logged-in user
- Logout
- Protect the dashboard so only logged-in users can access it

## Current Routes

- Dashboard: `http://127.0.0.1:5000/`
- Login: `http://127.0.0.1:5000/login`
- Register: `http://127.0.0.1:5000/register`
- Logout: `http://127.0.0.1:5000/logout`

## Notes

- MySQL is used by the Login/Register module only at this stage.
- The other database tables are included in `schema.sql` for future modules.
- This is still a simple beginner-friendly module.
- Inventory modules are not created yet.
