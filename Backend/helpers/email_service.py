import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import Optional
from config.settings import settings
from models.appointment import Appointment
from models.caller import Caller

async def send_confirmation_email(appointment: Appointment) -> bool:
    sender_email = settings.SENDER_EMAIL or settings.GMAIL_USER
    sender_password = settings.SENDER_PASSWORD or settings.GMAIL_PASSWORD
    sender_name = settings.SENDER_NAME or "Legal Intake Team"
    
    if not sender_email or not sender_password:
        print(f"[ERROR] Email credentials not configured. SENDER_EMAIL={bool(sender_email)}, SENDER_PASSWORD={bool(sender_password)}")
        return False
    
    try:
        caller = await Caller.get(id=appointment.caller_id)
        
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Appointment Confirmation - {appointment.practice_area}"
        msg['From'] = f"{sender_name} <{sender_email}>"
        msg['To'] = caller.email
        
        appointment_datetime = appointment.appointment_date
        formatted_date = appointment_datetime.strftime("%B %d, %Y")
        formatted_time = appointment_datetime.strftime("%I:%M %p")
        
        html_body = f"""
        <html>
          <body>
            <h2>Appointment Confirmation</h2>
            <p>Dear {caller.full_name},</p>
            <p>This email confirms your appointment for a {appointment.practice_area} consultation.</p>
            <h3>Appointment Details:</h3>
            <ul>
              <li><strong>Date:</strong> {formatted_date}</li>
              <li><strong>Time:</strong> {formatted_time}</li>
              <li><strong>Practice Area:</strong> {appointment.practice_area}</li>
            </ul>
            <h3>Next Steps:</h3>
            <p>Please arrive 10 minutes early for your appointment. If you need to reschedule or cancel, please contact us at least 24 hours in advance.</p>
            <p>If you have any questions, please don't hesitate to reach out.</p>
            <p>Best regards,<br>Legal Intake Team</p>
          </body>
        </html>
        """
        
        text_body = f"""
        Appointment Confirmation
        
        Dear {caller.full_name},
        
        This email confirms your appointment for a {appointment.practice_area} consultation.
        
        Appointment Details:
        - Date: {formatted_date}
        - Time: {formatted_time}
        - Practice Area: {appointment.practice_area}
        
        Next Steps:
        Please arrive 10 minutes early for your appointment. If you need to reschedule or cancel, please contact us at least 24 hours in advance.
        
        If you have any questions, please don't hesitate to reach out.
        
        Best regards,
        Legal Intake Team
        """
        
        part1 = MIMEText(text_body, 'plain')
        part2 = MIMEText(html_body, 'html')
        
        msg.attach(part1)
        msg.attach(part2)
        
        print(f"[EMAIL] Sending confirmation email from {sender_email} to {caller.email}")
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
        print(f"[EMAIL] Confirmation email sent successfully to {caller.email}")
        
        appointment.confirmation_email_sent = True
        await appointment.save()
        
        return True
        
    except smtplib.SMTPAuthenticationError as auth_error:
        print(f"[ERROR] Email authentication failed: {auth_error}")
        print(f"[ERROR] Please verify SENDER_EMAIL and SENDER_PASSWORD in .env file")
        return False
    except smtplib.SMTPException as smtp_error:
        print(f"[ERROR] SMTP error sending email: {smtp_error}")
        return False
    except Exception as e:
        print(f"[ERROR] Error sending confirmation email: {e}")
        import traceback
        traceback.print_exc()
        return False

