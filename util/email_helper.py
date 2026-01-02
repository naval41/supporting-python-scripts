import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import List, Optional, Union, Dict, Any
from email.utils import formataddr
from .config import Config

class EmailHelper:
    def __init__(self, email_config: Optional[Dict[str, Any]] = None):
        self.config = email_config or Config.get_email_config()
        self.smtp_server = self.config.get("smtp_server")
        self.smtp_port = self.config.get("smtp_port")
        self.sender_email = self.config.get("sender_email")
        self.sender_name = self.config.get("sender_name")
        self.sender_password = self.config.get("sender_password")

    def send_email(self, 
                   subject: str, 
                   body: str, 
                   recipients: Union[str, List[str]], 
                   is_html: bool = False):
        """
        Send an email to one or multiple recipients.
        """
        if not all([self.smtp_server, self.smtp_port, self.sender_email, self.sender_password]):
            print("Email configuration is incomplete.")
            return False

        if isinstance(recipients, str):
            recipients = [recipients]

        msg = MIMEMultipart()
        if self.sender_name:
            msg['From'] = formataddr((self.sender_name, self.sender_email))
        else:
            msg['From'] = self.sender_email
            
        msg['To'] = ", ".join(recipients)
        msg['Subject'] = subject

        msg.attach(MIMEText(body, 'html' if is_html else 'plain'))

        try:
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.sender_email, self.sender_password)
            server.sendmail(self.sender_email, recipients, msg.as_string())
            server.quit()
            return True
        except Exception as e:
            print(f"Failed to send email: {e}")
            return False
