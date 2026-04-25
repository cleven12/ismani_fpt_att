from flask import Flask, render_template, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail, Message
from datetime import datetime, date
from dotenv import load_dotenv
import hashlib
import os

load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'change-this-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///attendance.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Gmail SMTP config
app.config['MAIL_SERVER'] = 'mail.visitkili.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.getenv('MAIL_USERNAME')

db = SQLAlchemy(app)
mail = Mail(app)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    reg_number = db.Column(db.String(50), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)
    company = db.Column(db.String(100), nullable=False)
    device_fingerprint = db.Column(db.String(64), nullable=False)
    ip_address = db.Column(db.String(45), nullable=False)
    user_agent = db.Column(db.Text, nullable=False)
    screen_resolution = db.Column(db.String(20))
    timezone = db.Column(db.String(50))
    language = db.Column(db.String(20))
    latitude = db.Column(db.String(20))
    longitude = db.Column(db.String(20))
    submitted_at = db.Column(db.DateTime, default=datetime.now)
    date_only = db.Column(db.Date, default=date.today)

    def to_dict(self):
        return {
            'reg_number': self.reg_number,
            'full_name': self.full_name,
            'company': self.company,
            'submitted_at': self.submitted_at.strftime('%Y-%m-%d %H:%M:%S'),
            'ip_address': self.ip_address,
        }


def get_ip():
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    return request.remote_addr


def build_fingerprint(data: dict) -> str:
    raw = f"{data.get('user_agent')}{data.get('screen_resolution')}{data.get('timezone')}{data.get('language')}{data.get('canvas_hash')}"
    return hashlib.sha256(raw.encode()).hexdigest()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/submit', methods=['POST'])
def submit():
    data = request.get_json()

    reg_number = data.get('reg_number', '').strip().upper()
    full_name = data.get('full_name', '').strip()
    company = data.get('company', '').strip()
    user_agent = request.headers.get('User-Agent', '')
    ip = get_ip()
    today = date.today()

    if not reg_number or not full_name or not company:
        return jsonify({'success': False, 'message': 'All fields are required.'}), 400

    # Build device fingerprint
    fingerprint_data = {
        'user_agent': user_agent,
        'screen_resolution': data.get('screen_resolution', ''),
        'timezone': data.get('timezone', ''),
        'language': data.get('language', ''),
        'canvas_hash': data.get('canvas_hash', ''),
    }
    fingerprint = build_fingerprint(fingerprint_data)

    # Check 1: has this device already submitted today?
    device_today = Attendance.query.filter_by(
        device_fingerprint=fingerprint,
        date_only=today
    ).first()

    if device_today:
        return jsonify({
            'success': False,
            'message': f'This device already submitted attendance today for {device_today.reg_number}. One submission per device per day.'
        }), 403

    # Check 2: has this reg number already submitted today?
    reg_today = Attendance.query.filter_by(
        reg_number=reg_number,
        date_only=today
    ).first()

    if reg_today:
        return jsonify({
            'success': False,
            'message': f'Attendance for {reg_number} already recorded today.'
        }), 403

    # Save to DB
    record = Attendance(
        reg_number=reg_number,
        full_name=full_name,
        company=company,
        device_fingerprint=fingerprint,
        ip_address=ip,
        user_agent=user_agent,
        screen_resolution=data.get('screen_resolution', ''),
        timezone=data.get('timezone', ''),
        language=data.get('language', ''),
        latitude=data.get('latitude', ''),
        longitude=data.get('longitude', ''),
        date_only=today
    )
    db.session.add(record)
    db.session.commit()

    # Send email alert
    try:
        msg = Message(
            subject=f'[FPT Attendance] {reg_number} — {today}',
            recipients=[os.getenv('NOTIFY_EMAIL')],
            body=f"""
New FPT Attendance Submission
==============================
Name:        {full_name}
Reg Number:  {reg_number}
Company:     {company}
Time:        {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} UTC
IP Address:  {ip}
Device:      {user_agent[:80]}
Resolution:  {data.get('screen_resolution', 'N/A')}
Timezone:    {data.get('timezone', 'N/A')}
Location:    {data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}
Fingerprint: {fingerprint[:16]}...
"""
        )
        mail.send(msg)
    except Exception as e:
        print(f"Mail error: {e}")  # don't fail the request if mail fails

    return jsonify({
        'success': True,
        'message': f'Attendance recorded successfully. Welcome, {full_name}!'
    })


@app.route('/admin')
def admin():
    # basic — protect this with auth later
    token = request.args.get('token')
    if token != os.getenv('ADMIN_TOKEN', 'changeme'):
        return 'Unauthorized', 401

    today = date.today()
    records = Attendance.query.filter_by(date_only=today).order_by(Attendance.submitted_at.desc()).all()
    all_records = Attendance.query.order_by(Attendance.submitted_at.desc()).limit(100).all()
    return render_template('admin.html', records=records, all_records=all_records, today=today)


with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=False)


"""
import os
import sys


sys.path.insert(0, os.path.dirname(__file__))


def app(environ, start_response):
    start_response('200 OK', [('Content-Type', 'text/plain')])
    message = 'It works!\n'
    version = 'Python v' + sys.version.split()[0] + '\n'
    response = '\n'.join([message, version])
    return [response.encode()]
"""