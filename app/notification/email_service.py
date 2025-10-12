from flask_mail import Message
from app.extensions import mail

def send_email(to_email, subject, body_html):
    msg = Message(
        subject=subject,
        recipients=[to_email],
        html=body_html
    )
    mail.send(msg)
