"""
Email Service with Templates
Sends transactional emails (welcome, alerts, notifications)
"""
import os
from typing import Optional, List, Dict, Any
from pathlib import Path
import aiosmtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader
from backend.utils.logger import logger

# Email configuration
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD")
SMTP_FROM_EMAIL = os.getenv("SMTP_FROM_EMAIL", SMTP_USER)
SMTP_FROM_NAME = os.getenv("SMTP_FROM_NAME", "VintedBot")

# Template directory
TEMPLATE_DIR = Path(__file__).parent.parent / "email_templates"
TEMPLATE_DIR.mkdir(parents=True, exist_ok=True)

# Jinja2 environment
jinja_env = Environment(loader=FileSystemLoader(str(TEMPLATE_DIR)))


class EmailService:
    """
    Production-ready email service

    Features:
    - HTML + Plain text emails
    - Jinja2 templates
    - Async sending
    - Error handling
    - Template validation
    """

    def __init__(self):
        self.smtp_host = SMTP_HOST
        self.smtp_port = SMTP_PORT
        self.smtp_user = SMTP_USER
        self.smtp_password = SMTP_PASSWORD
        self.from_email = SMTP_FROM_EMAIL
        self.from_name = SMTP_FROM_NAME

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None
    ) -> bool:
        """
        Send email

        Args:
            to_email: Recipient email
            subject: Email subject
            html_content: HTML body
            text_content: Plain text body (optional)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP not configured - email not sent")
            return False

        try:
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = subject
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email

            # Add text version
            if text_content:
                part1 = MIMEText(text_content, "plain")
                message.attach(part1)

            # Add HTML version
            part2 = MIMEText(html_content, "html")
            message.attach(part2)

            # Send via SMTP
            await aiosmtplib.send(
                message,
                hostname=self.smtp_host,
                port=self.smtp_port,
                username=self.smtp_user,
                password=self.smtp_password,
                start_tls=True,
            )

            logger.info(f"[OK] Email sent to {to_email}: {subject}")
            return True

        except Exception as e:
            logger.error(f"[ERROR] Email send failed to {to_email}: {e}")
            return False

    async def send_template_email(
        self,
        to_email: str,
        subject: str,
        template_name: str,
        context: Dict[str, Any]
    ) -> bool:
        """
        Send email using Jinja2 template

        Args:
            to_email: Recipient email
            subject: Email subject
            template_name: Template filename (e.g., "welcome.html")
            context: Template variables

        Returns:
            True if sent successfully
        """
        try:
            # Render template
            template = jinja_env.get_template(template_name)
            html_content = template.render(**context)

            # Generate plain text version (strip HTML tags)
            import re
            text_content = re.sub('<[^<]+?>', '', html_content)

            return await self.send_email(to_email, subject, html_content, text_content)

        except Exception as e:
            logger.error(f"[ERROR] Template email failed: {e}")
            return False

    # ============================================================================
    # TRANSACTIONAL EMAILS
    # ============================================================================

    async def send_welcome_email(self, email: str, username: str) -> bool:
        """Send welcome email to new user"""
        return await self.send_template_email(
            to_email=email,
            subject="Bienvenue sur VintedBot ! [START]",
            template_name="welcome.html",
            context={
                "username": username,
                "login_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/login",
                "dashboard_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard",
            }
        )

    async def send_quota_alert(self, email: str, username: str, quota_type: str, used: int, limit: int) -> bool:
        """Send quota limit alert"""
        return await self.send_template_email(
            to_email=email,
            subject=f"[WARN] Limite de quota atteinte - {quota_type}",
            template_name="quota_alert.html",
            context={
                "username": username,
                "quota_type": quota_type,
                "used": used,
                "limit": limit,
                "percentage": int((used / limit) * 100),
                "upgrade_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/settings?tab=billing",
            }
        )

    async def send_error_alert(self, email: str, username: str, error_message: str) -> bool:
        """Send error alert to user"""
        return await self.send_template_email(
            to_email=email,
            subject="[ERROR] Erreur dans votre automatisation VintedBot",
            template_name="error_alert.html",
            context={
                "username": username,
                "error_message": error_message,
                "support_url": "https://vintedbots.com/support",
            }
        )

    async def send_payment_confirmation(self, email: str, username: str, plan: str, amount: float) -> bool:
        """Send payment confirmation"""
        return await self.send_template_email(
            to_email=email,
            subject=f"[OK] Paiement confirmé - Plan {plan}",
            template_name="payment_confirmation.html",
            context={
                "username": username,
                "plan": plan,
                "amount": amount,
                "invoice_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/settings?tab=billing",
            }
        )

    async def send_captcha_alert(self, email: str, username: str, account_name: str) -> bool:
        """Send captcha detection alert"""
        return await self.send_template_email(
            to_email=email,
            subject="[WARN] Captcha détecté sur votre compte Vinted",
            template_name="captcha_alert.html",
            context={
                "username": username,
                "account_name": account_name,
                "dashboard_url": f"{os.getenv('FRONTEND_URL', 'http://localhost:3000')}/dashboard",
            }
        )


# Global email service instance
email_service = EmailService()


# ============================================================================
# CREATE DEFAULT EMAIL TEMPLATES
# ============================================================================

def create_default_templates():
    """Create default email templates if they don't exist"""

    # Welcome email template
    welcome_template = """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
        .footer { text-align: center; margin-top: 30px; color: #666; font-size: 12px; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>[START] Bienvenue sur VintedBot !</h1>
        </div>
        <div class="content">
            <h2>Bonjour {{ username }},</h2>
            <p>Merci de vous être inscrit sur VintedBot, le bot Vinted le plus sophistiqué du marché !</p>
            <p>Voici ce que vous pouvez faire dès maintenant :</p>
            <ul>
                <li>[PHOTO] Analyser vos photos avec l'IA GPT-4 Vision</li>
                <li>📊 Suivre vos performances dans le dashboard analytics</li>
                <li>🤖 Automatiser vos bumps, follows et messages</li>
            </ul>
            <a href="{{ dashboard_url }}" class="button">Accéder au Dashboard</a>
            <p><strong>Important :</strong> N'oubliez pas que l'utilisation de bots viole les conditions d'utilisation de Vinted et peut entraîner le bannissement de votre compte.</p>
        </div>
        <div class="footer">
            <p>VintedBot - L'automatisation Vinted la plus avancée</p>
        </div>
    </div>
</body>
</html>"""

    # Quota alert template
    quota_alert_template = """<!DOCTYPE html>
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
        .container { max-width: 600px; margin: 0 auto; padding: 20px; }
        .header { background: #f59e0b; color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
        .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
        .progress { background: #ddd; height: 20px; border-radius: 10px; overflow: hidden; }
        .progress-bar { background: #f59e0b; height: 100%; }
        .button { display: inline-block; background: #667eea; color: white; padding: 12px 30px; text-decoration: none; border-radius: 5px; margin: 20px 0; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>[WARN] Limite de quota atteinte</h1>
        </div>
        <div class="content">
            <h2>Bonjour {{ username }},</h2>
            <p>Vous avez atteint <strong>{{ percentage }}%</strong> de votre quota <strong>{{ quota_type }}</strong>.</p>
            <div class="progress">
                <div class="progress-bar" style="width: {{ percentage }}%"></div>
            </div>
            <p><strong>{{ used }}</strong> / {{ limit }} utilisés</p>
            <p>Passez à un plan supérieur pour continuer à utiliser VintedBot sans limites !</p>
            <a href="{{ upgrade_url }}" class="button">Voir les Plans</a>
        </div>
    </div>
</body>
</html>"""

    # Write templates
    templates = {
        "welcome.html": welcome_template,
        "quota_alert.html": quota_alert_template,
    }

    for filename, content in templates.items():
        template_path = TEMPLATE_DIR / filename
        if not template_path.exists():
            template_path.write_text(content)
            logger.info(f"Created email template: {filename}")


# Create templates on import
create_default_templates()
