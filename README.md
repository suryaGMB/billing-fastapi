# 🧾 Billing System - FastAPI Mini Project

### 📌 Description
This is a small **Billing Web Application** built using **FastAPI**, **SQLModel**, and **Jinja2 templates**.

The app allows:
- Creating customer bills
- Adding multiple products
- Calculating total, tax, and balance change
- Showing denomination breakdown
- Sending (simulated) invoice emails
- Viewing the generated invoice preview
- Resetting to create a new bill

---

### ⚙️ Tech Stack
- **Backend:** FastAPI, SQLModel
- **Frontend:** HTML, CSS, JavaScript
- **Templating:** Jinja2
- **Database:** SQLite (local file)
- **Async Email:** aiosmtplib (optional, can be left unconfigured)

---

### Instructions to Run the Project

- Clone or Download the Project
- cd billing-fastapi
- python -m venv .venv
- .\.venv\Scripts\activate
- pip install -r requirements.txt
- create .env file

DATABASE_URL=sqlite:///./billing.db

# Email config (optional)
SMTP_HOST=
SMTP_PORT=587
SMTP_USER=
SMTP_PASS=
FROM_EMAIL=no-reply@example.com

- python -m app.email_utils

## 🧠 PowerShell Script Policy (Windows Users)

If you're running this project on **Windows PowerShell**, you may see this error while activating the virtual environment:

### ✅ Fix
To allow PowerShell to run virtual environment activation scripts, run this **once** (no admin needed):

```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# Run the FastAPI Server
- uvicorn app.main:app --reload
