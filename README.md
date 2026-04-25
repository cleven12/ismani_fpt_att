# FPT Attendance System
**fpt.isamanitours.com** — Field Practical Training attendance tracker

Built for: Isamani Tours & Safari / Visit Kili Adventures / Kilinge Adventures

---

## Features

- Trainee fills name, reg number, company
- Device fingerprint captured (canvas, screen, timezone, language, user agent)
- IP address logged
- Geolocation (if trainee allows)
- One submission per device per day — blocks proxy submissions
- One submission per reg number per day
- Email alert sent to supervisor on each submission
- Admin dashboard at `/admin?token=yourtoken`

---

## Local Setup

```bash
git clone https://github.com/cleven12/ismani_fpt_att
cd ismani_fpt_att

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# edit .env with your Gmail app password and tokens

python app.py
```

Visit `http://localhost:5000`

---

## Gmail App Password

1. Go to myaccount.google.com → Security
2. Enable 2-Step Verification
3. Search "App passwords" → create one for "Mail"
4. Paste that 16-char password into `MAIL_PASSWORD` in `.env`

---



## Admin Access

```
https://v2.visitkili.com/admin?token=yourtoken
```

Set `ADMIN_TOKEN` in `.env` to something strong.

---

## Repo Structure

```
ismani_fpt_att/
├── app.py              ← main Flask app
├── requirements.txt
├── .env.example
├── templates/
│   ├── index.html      ← attendance form
│   └── admin.html      ← supervisor dashboard
└── instance/
    └── attendance.db   ← SQLite DB (auto-created)
```