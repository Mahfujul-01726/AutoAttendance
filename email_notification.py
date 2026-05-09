import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from config import EMAIL_ADDRESS, EMAIL_PASSWORD, SMTP_SERVER, SMTP_PORT

class EmailNotificationModule:
    """Sends email notifications for attendance"""
    
    @staticmethod
    def send_attendance_report(recipient_email, name, date, time, status="Present"):
        """
        Send attendance report via email
        
        Args:
            recipient_email: Student/Person email
            name: Person's name
            date: Attendance date
            time: Attendance time
            status: Attendance status
        """
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = recipient_email
            msg['Subject'] = f"Attendance Report - {date}"
            
            # Email body
            body = f"""
            Dear {name},
            
            Your attendance has been recorded:
            
            Date: {date}
            Time: {time}
            Status: {status}
            
            If you did not expect this notification or have concerns about your attendance,
            please contact the administration immediately.
            
            Best regards,
            Automated Attendance System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_ADDRESS, recipient_email, text)
            server.quit()
            
            print(f"Email sent to {recipient_email}")
            return True
            
        except Exception as e:
            print(f"Error sending email: {e}")
            return False
    
    @staticmethod
    def send_intruder_alert(admin_email, detected_person, timestamp):
        """
        Send alert about intruder/unknown person
        
        Args:
            admin_email: Administrator email
            detected_person: Description of detected person
            timestamp: When intruder was detected
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = admin_email
            msg['Subject'] = "SECURITY ALERT: Intruder Detected!"
            
            body = f"""
            SECURITY ALERT
            
            An unknown or unauthorized person has been detected in the system:
            
            Description: {detected_person}
            Timestamp: {timestamp}
            
            Please investigate immediately.
            
            Automated Attendance System
            """
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_ADDRESS, admin_email, text)
            server.quit()
            
            print(f"Alert email sent to {admin_email}")
            return True
            
        except Exception as e:
            print(f"Error sending alert: {e}")
            return False
    
    @staticmethod
    def send_daily_report(admin_email, attendance_data):
        """
        Send daily attendance summary
        
        Args:
            admin_email: Administrator email
            attendance_data: Dictionary with attendance information
        """
        try:
            msg = MIMEMultipart()
            msg['From'] = EMAIL_ADDRESS
            msg['To'] = admin_email
            msg['Subject'] = f"Daily Attendance Report - {datetime.now().strftime('%Y-%m-%d')}"
            
            # Create report body
            body = "DAILY ATTENDANCE REPORT\n\n"
            body += f"Date: {datetime.now().strftime('%Y-%m-%d')}\n"
            body += f"Total Present: {len(attendance_data)}\n\n"
            body += "Attendance Details:\n"
            body += "-" * 50 + "\n"
            
            for person, details in attendance_data.items():
                body += f"Name: {person}\n"
                body += f"Time: {details['time']}\n"
                body += f"Status: {details['status']}\n"
                body += "-" * 50 + "\n"
            
            msg.attach(MIMEText(body, 'plain'))
            
            server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
            server.starttls()
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            text = msg.as_string()
            server.sendmail(EMAIL_ADDRESS, admin_email, text)
            server.quit()
            
            print(f"Daily report sent to {admin_email}")
            return True
            
        except Exception as e:
            print(f"Error sending report: {e}")
            return False
