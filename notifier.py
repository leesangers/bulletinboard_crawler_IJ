import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os


class EmailNotifier:
    def __init__(self, smtp_server="smtp.gmail.com", port=587):
        self.smtp_server = smtp_server
        self.port = port
        self.email_user = os.getenv("EMAIL_USER")
        self.email_pw = os.getenv("EMAIL_APP_PASSWORD")
        self.recipient_email = os.getenv("RECIPIENT_EMAIL")

    def send_notification(self, posts, fda_error=False):
        """
        Sends an email with new FDA press announcements.
        Always sends even when there are no new posts.
        Supports multiple recipients via comma-separated RECIPIENT_EMAIL.
        """
        if not self.email_user or not self.email_pw or not self.recipient_email:
            print("Email credentials or recipient not configured in environment variables.")
            return False

        recipients = [r.strip() for r in self.recipient_email.split(",") if r.strip()]

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_user
            msg["To"] = self.email_user

            if fda_error:
                msg["Subject"] = "[FDA Alert] Error fetching press announcements"
            elif posts:
                msg["Subject"] = f"[FDA Alert] {len(posts)} new press announcement(s)"
            else:
                msg["Subject"] = "[FDA Alert] No new press announcements"

            html = "<h2>FDA Press Announcements Monitor</h2>"

            if fda_error:
                html += "<p style='color: #d93025; font-weight: bold;'>⚠️ Failed to fetch data from the FDA website. Please check the crawler.</p>"
            elif not posts:
                html += "<p style='color: #70757a;'>No new press announcements in the last 3 days.</p>"
            else:
                html += "<table border='1' cellpadding='5' style='border-collapse: collapse; width: 100%;'>"
                html += "<thead><tr style='background-color: #f2f2f2;'><th>Date</th><th>Title</th></tr></thead>"
                html += "<tbody>"
                for post in posts:
                    link_style = "color: #1a73e8; text-decoration: none; font-weight: bold;"
                    html += (
                        f"<tr>"
                        f"<td style='white-space: nowrap;'>{post['date']}</td>"
                        f"<td><a href='{post['url']}' style='{link_style}'>{post['title']}</a></td>"
                        f"</tr>"
                    )
                html += "</tbody></table>"

            html += "<br/><p style='color: grey;'>This email was sent automatically.</p>"

            msg.attach(MIMEText(html, "html"))

            with smtplib.SMTP(self.smtp_server, self.port) as server:
                server.starttls()
                server.login(self.email_user, self.email_pw)
                server.sendmail(self.email_user, recipients, msg.as_string())

            print(f"Notification sent to {len(recipients)} recipient(s): {', '.join(recipients)}")
            return True

        except Exception as e:
            print(f"FAILED to send email: {e}")
            import traceback
            traceback.print_exc()
            return False
