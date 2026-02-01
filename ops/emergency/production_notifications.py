"""
Production Notification Handlers with Real API Integrations

This module provides real implementations of notification handlers that replace
the mock handlers for production use. Each handler uses live API credentials
from environment variables.
"""
import os
import smtplib
import requests
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any
from datetime import datetime
from pathlib import Path
import json
import logging

# Import from existing notifications.py
from notifications import (
    NotificationType,
    NotificationResult,
    MockNotificationHandler
)

# Try to import Firebase Admin SDK
try:
    import firebase_admin
    from firebase_admin import credentials, messaging
    FIREBASE_AVAILABLE = True
except ImportError:
    FIREBASE_AVAILABLE = False
    logging.warning("Firebase Admin SDK not installed. Install with: pip install firebase-admin")

# Try to import Twilio SDK
try:
    from twilio.rest import Client
    TWILIO_AVAILABLE = True
except ImportError:
    TWILIO_AVAILABLE = False
    logging.warning("Twilio SDK not installed. Install with: pip install twilio")


class SMTPEmailHandler(MockNotificationHandler):
    """Production email handler using SMTP."""
    
    def __init__(self):
        super().__init__()
        self.smtp_host = os.getenv("SMTP_HOST", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("SMTP_FROM_EMAIL", "noreply@proharp.com")
        self.from_name = os.getenv("SMTP_FROM_NAME", "Pro-Harp Security")
        
        # Validate configuration
        if not self.smtp_username or not self.smtp_password:
            self.logger.warning("SMTP credentials not configured. Falling back to mock mode.")
            self.enabled = False
        else:
            self.enabled = True
            self.logger.info(f"SMTP Email Handler initialized: {self.smtp_host}:{self.smtp_port}")
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """Send email via SMTP."""
        if not self.enabled:
            self.logger.warning("SMTP not configured. Sending mock email.")
            return super().send(recipient, message, metadata)
        
        try:
            # Extract subject from metadata or use default
            subject = metadata.get("subject", "Pro-Harp Security Alert") if metadata else "Pro-Harp Security Alert"
            
            # Create message
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.from_name} <{self.from_email}>"
            msg["To"] = recipient
            
            # Plain text body
            text_body = message
            
            # HTML body (enhanced formatting)
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; padding: 20px;">
                <div style="background-color: #f8f9fa; border-left: 4px solid #dc3545; padding: 15px;">
                  <h2 style="color: #dc3545; margin-top: 0;">{subject}</h2>
                  <p style="color: #333; line-height: 1.6;">{message}</p>
                  {self._format_metadata_html(metadata) if metadata else ""}
                </div>
                <p style="color: #6c757d; font-size: 12px; margin-top: 20px;">
                  This is an automated message from Pro-Harp Emergency Response System.
                </p>
              </body>
            </html>
            """
            
            msg.attach(MIMEText(text_body, "plain"))
            msg.attach(MIMEText(html_body, "html"))
            
            # Send via SMTP
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            self.logger.info(f"[SMTP EMAIL] Sent to {recipient}: {subject}")
            
            result = NotificationResult(
                success=True,
                notification_type=NotificationType.EMAIL,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            self._log_to_file(result)
            return result
            
        except Exception as e:
            self.logger.error(f"[SMTP EMAIL] Failed to send to {recipient}: {e}")
            return NotificationResult(
                success=False,
                notification_type=NotificationType.EMAIL,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                error=str(e),
                metadata=metadata
            )
    
    def _format_metadata_html(self, metadata: Dict[str, Any]) -> str:
        """Format metadata as HTML table."""
        if not metadata:
            return ""
        
        rows = []
        for key, value in metadata.items():
            if key != "subject":  # Skip subject as it's already in the header
                rows.append(f"<tr><td><strong>{key}:</strong></td><td>{value}</td></tr>")
        
        if rows:
            return f"""
            <table style="margin-top: 15px; border-collapse: collapse;">
              {''.join(rows)}
            </table>
            """
        return ""


class TwilioSMSHandler(MockNotificationHandler):
    """Production SMS handler using Twilio."""
    
    def __init__(self):
        super().__init__()
        if not TWILIO_AVAILABLE:
            self.enabled = False
            self.logger.warning("Twilio SDK not available. Falling back to mock mode.")
            return
            
        self.account_sid = os.getenv("TWILIO_ACCOUNT_SID")
        self.auth_token = os.getenv("TWILIO_AUTH_TOKEN")
        self.from_number = os.getenv("TWILIO_PHONE_NUMBER")
        
        if not all([self.account_sid, self.auth_token, self.from_number]):
            self.enabled = False
            self.logger.warning("Twilio credentials not configured. Falling back to mock mode.")
        else:
            self.client = Client(self.account_sid, self.auth_token)
            self.enabled = True
            self.logger.info(f"Twilio SMS Handler initialized: {self.from_number}")
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """Send SMS via Twilio."""
        if not self.enabled:
            self.logger.warning("Twilio not configured. Sending mock SMS.")
            return super().send(recipient, message, metadata)
        
        try:
            # Twilio SMS has 160 character limit for single message
            # Truncate if necessary
            sms_message = message[:160]
            
            # Send SMS
            twilio_message = self.client.messages.create(
                body=sms_message,
                from_=self.from_number,
                to=recipient
            )
            
            self.logger.info(f"[TWILIO SMS] Sent to {recipient}: SID {twilio_message.sid}")
            
            result = NotificationResult(
                success=True,
                notification_type=NotificationType.SMS,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                metadata={**(metadata or {}), "twilio_sid": twilio_message.sid}
            )
            
            self._log_to_file(result)
            return result
            
        except Exception as e:
            self.logger.error(f"[TWILIO SMS] Failed to send to {recipient}: {e}")
            return NotificationResult(
                success=False,
                notification_type=NotificationType.SMS,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                error=str(e),
                metadata=metadata
            )


class FirebasePushHandler(MockNotificationHandler):
    """Production push notification handler using Firebase Cloud Messaging."""
    
    def __init__(self):
        super().__init__()
        if not FIREBASE_AVAILABLE:
            self.enabled = False
            self.logger.warning("Firebase Admin SDK not available. Falling back to mock mode.")
            return
        
        firebase_cred_path = os.getenv("FIREBASE_SERVICE_ACCOUNT_PATH")
        
        if not firebase_cred_path or not Path(firebase_cred_path).exists():
            self.enabled = False
            self.logger.warning("Firebase service account not found. Falling back to mock mode.")
            return
        
        try:
            # Initialize Firebase Admin SDK
            if not firebase_admin._apps:
                cred = credentials.Certificate(firebase_cred_path)
                firebase_admin.initialize_app(cred)
            
            self.enabled = True
            self.logger.info("Firebase Push Notification Handler initialized")
        except Exception as e:
            self.enabled = False
            self.logger.error(f"Failed to initialize Firebase: {e}")
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """Send push notification via Firebase Cloud Messaging."""
        if not self.enabled:
            self.logger.warning("Firebase not configured. Sending mock push notification.")
            return super().send(recipient, message, metadata)
        
        try:
            # Extract notification details from metadata
            title = metadata.get("title", "Pro-Harp Alert") if metadata else "Pro-Harp Alert"
            priority = metadata.get("priority", "high") if metadata else "high"
            
            # Create FCM message
            fcm_message = messaging.Message(
                notification=messaging.Notification(
                    title=title,
                    body=message
                ),
                data=metadata or {},
                token=recipient,
                android=messaging.AndroidConfig(
                    priority=priority,
                    notification=messaging.AndroidNotification(
                        sound="default",
                        color="#dc3545"  # Red for alerts
                    )
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound="default",
                            badge=1
                        )
                    )
                )
            )
            
            # Send message
            response = messaging.send(fcm_message)
            
            self.logger.info(f"[FIREBASE PUSH] Sent to device: {recipient[:20]}... | Message ID: {response}")
            
            result = NotificationResult(
                success=True,
                notification_type=NotificationType.PUSH,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                metadata={**(metadata or {}), "fcm_message_id": response}
            )
            
            self._log_to_file(result)
            return result
            
        except Exception as e:
            self.logger.error(f"[FIREBASE PUSH] Failed to send: {e}")
            return NotificationResult(
                success=False,
                notification_type=NotificationType.PUSH,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                error=str(e),
                metadata=metadata
            )


class SlackWebhookHandler(MockNotificationHandler):
    """Production ChatOps handler using Slack webhooks."""
    
    def __init__(self):
        super().__init__()
        self.webhook_url = os.getenv("SLACK_WEBHOOK_URL")
        
        if not self.webhook_url or "your_slack_webhook" in self.webhook_url:
            self.enabled = False
            self.logger.warning("Slack webhook not configured. Falling back to mock mode.")
        else:
            self.enabled = True
            self.logger.info("Slack Webhook Handler initialized")
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """Send message to Slack via webhook."""
        if not self.enabled:
            self.logger.warning("Slack webhook not configured. Sending mock ChatOps notification.")
            return super().send(recipient, message, metadata)
        
        try:
            # Format message for Slack
            slack_payload = {
                "text": f"*Pro-Harp Security Alert*",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": "🚨 Pro-Harp Security Alert"
                        }
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": message
                        }
                    }
                ]
            }
            
            # Add metadata fields if available
            if metadata:
                fields = []
                for key, value in metadata.items():
                    fields.append({
                        "type": "mrkdwn",
                        "text": f"*{key}:*\n{value}"
                    })
                
                if fields:
                    slack_payload["blocks"].append({
                        "type": "section",
                        "fields": fields[:10]  # Slack limits to 10 fields
                    })
            
            # Send to Slack
            response = requests.post(
                self.webhook_url,
                json=slack_payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            self.logger.info(f"[SLACK] Sent to {recipient} | Status: {response.status_code}")
            
            result = NotificationResult(
                success=True,
                notification_type=NotificationType.CHATOPS,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            self._log_to_file(result)
            return result
            
        except Exception as e:
            self.logger.error(f"[SLACK] Failed to send: {e}")
            return NotificationResult(
                success=False,
                notification_type=NotificationType.CHATOPS,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                error=str(e),
                metadata=metadata
            )


class TeamsWebhookHandler(MockNotificationHandler):
    """Production ChatOps handler using Microsoft Teams webhooks."""
    
    def __init__(self):
        super().__init__()
        self.webhook_url = os.getenv("TEAMS_WEBHOOK_URL")
        
        if not self.webhook_url or "your_teams_webhook" in self.webhook_url:
            self.enabled = False
            self.logger.warning("Teams webhook not configured. Falling back to mock mode.")
        else:
            self.enabled = True
            self.logger.info("Teams Webhook Handler initialized")
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """Send message to Teams via webhook."""
        if not self.enabled:
            self.logger.warning("Teams webhook not configured. Sending mock ChatOps notification.")
            return super().send(recipient, message, metadata)
        
        try:
            # Format message for Teams (Adaptive Card format)
            teams_payload = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "dc3545",
                "summary": "Pro-Harp Security Alert",
                "sections": [{
                    "activityTitle": "🚨 Pro-Harp Security Alert",
                    "text": message,
                    "facts": [
                        {"name": key, "value": str(value)}
                        for key, value in (metadata or {}).items()
                    ]
                }]
            }
            
            # Send to Teams
            response = requests.post(
                self.webhook_url,
                json=teams_payload,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            
            self.logger.info(f"[TEAMS] Sent to {recipient} | Status: {response.status_code}")
            
            result = NotificationResult(
                success=True,
                notification_type=NotificationType.CHATOPS,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                metadata=metadata
            )
            
            self._log_to_file(result)
            return result
            
        except Exception as e:
            self.logger.error(f"[TEAMS] Failed to send: {e}")
            return NotificationResult(
                success=False,
                notification_type=NotificationType.CHATOPS,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                error=str(e),
                metadata=metadata
            )
