"""
Notification dispatcher for emergency response system.

This module provides mock notification handlers that can be replaced with real
integrations (Twilio, FCM, Slack, etc.) when API credentials are available.
"""

import json
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class NotificationType(Enum):
    """Types of notifications."""
    SMS = "sms"
    VOICE = "voice"
    PUSH = "push"
    CHATOPS = "chatops"
    EMAIL = "email"


@dataclass
class NotificationResult:
    """Result of a notification attempt."""
    success: bool
    notification_type: NotificationType
    recipient: str
    message: str
    timestamp: datetime
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class MockNotificationHandler:
    """Base class for mock notification handlers."""
    
    def __init__(self, log_dir: str = "logs"):
        """
        Initialize notification handler.
        
        Args:
            log_dir: Directory for log files
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()
    
    def _setup_logger(self) -> logging.Logger:
        """Set up logger for notifications."""
        logger = logging.getLogger(f"notification.{self.__class__.__name__}")
        logger.setLevel(logging.INFO)
        
        # File handler
        handler = logging.FileHandler(self.log_dir / "notifications.log")
        handler.setFormatter(logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        ))
        logger.addHandler(handler)
        
        # Console handler
        console = logging.StreamHandler()
        console.setFormatter(logging.Formatter('%(levelname)s - %(message)s'))
        logger.addHandler(console)
        
        return logger
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """
        Send a notification (to be implemented by subclasses).
        
        Args:
            recipient: Recipient identifier
            message: Message content
            metadata: Additional metadata
            
        Returns:
            NotificationResult
        """
        raise NotImplementedError
    
    def _log_to_file(self, result: NotificationResult) -> None:
        """Log notification to JSONL file."""
        # Determine log filename from notification type
        log_filename = f"{result.notification_type.value}_notifications.jsonl"
        log_file = self.log_dir / log_filename
        
        with open(log_file, 'a') as f:
            f.write(json.dumps({
                "timestamp": result.timestamp.isoformat(),
                "type": result.notification_type.value,
                "recipient": result.recipient,
                "message": result.message,
                "success": result.success,
                "error": result.error,
                "metadata": result.metadata
            }) + "\n")


class MockSMSHandler(MockNotificationHandler):
    """Mock SMS notification handler."""
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """
        Send mock SMS notification.
        
        In production, this would integrate with Twilio, Vonage, etc.
        """
        self.logger.info(f"[MOCK SMS] To: {recipient} | Message: {message}")
        
        # Simulate sending
        result = NotificationResult(
            success=True,
            notification_type=NotificationType.SMS,
            recipient=recipient,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        # Log to file
        self._log_to_file(result)
        
        return result


class MockVoiceHandler(MockNotificationHandler):
    """Mock voice call notification handler."""
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """
        Send mock voice call notification.
        
        In production, this would integrate with Twilio Voice API.
        """
        self.logger.info(f"[MOCK VOICE CALL] To: {recipient} | Message: {message}")
        
        result = NotificationResult(
            success=True,
            notification_type=NotificationType.VOICE,
            recipient=recipient,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        self._log_to_file(result)
        
        return result


class MockPushHandler(MockNotificationHandler):
    """Mock push notification handler."""
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """
        Send mock push notification.
        
        In production, this would integrate with Firebase Cloud Messaging or APNs.
        """
        self.logger.info(f"[MOCK PUSH] To: {recipient} | Message: {message}")
        
        result = NotificationResult(
            success=True,
            notification_type=NotificationType.PUSH,
            recipient=recipient,
            message=message,
            timestamp=datetime.now(),
            metadata=metadata
        )
        
        self._log_to_file(result)
        
        return result


class MockChatOpsHandler(MockNotificationHandler):
    """Mock ChatOps notification handler (Slack, Teams, etc.)."""
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """
        Send mock ChatOps notification.
        
        In production, this would integrate with Slack webhooks, Teams connectors, etc.
        """
        self.logger.info(f"[MOCK CHATOPS] Channel: {recipient} | Message: {message}")
        
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


class MockEmailHandler(MockNotificationHandler):
    """Mock email notification handler."""
    
    def send(self, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """
        Send mock email notification.
        
        In production, this would integrate with SMTP or an email service (SendGrid, Mailgun, etc.).
        """
        self.logger.info(f"[MOCK EMAIL] To: {recipient} | Message: {message[:100]}...")
        
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


class NotificationDispatcher:
    """Main notification dispatcher with retry logic."""
    
    def __init__(self, retry_attempts: int = 3, retry_delay_seconds: int = 10, log_dir: str = "logs"):
        """
        Initialize notification dispatcher.
        
        Args:
            retry_attempts: Number of retry attempts for failed notifications
            retry_delay_seconds: Delay between retries
            log_dir: Directory for log files
        """
        self.retry_attempts = retry_attempts
        self.retry_delay_seconds = retry_delay_seconds
        self.log_dir = Path(log_dir)
        
        # Initialize handlers
        self.sms_handler = MockSMSHandler(log_dir)
        self.voice_handler = MockVoiceHandler(log_dir)
        self.push_handler = MockPushHandler(log_dir)
        self.chatops_handler = MockChatOpsHandler(log_dir)
        self.email_handler = MockEmailHandler(log_dir)
        
        self.logger = logging.getLogger("NotificationDispatcher")
        self.logger.setLevel(logging.INFO)
    
    def register_handler(self, notification_type: NotificationType, handler: MockNotificationHandler) -> None:
        """
        Register a notification handler for a specific type.
        
        Args:
            notification_type: Type of notification
            handler: Handler implementation
        """
        if notification_type == NotificationType.SMS:
            self.sms_handler = handler
        elif notification_type == NotificationType.VOICE:
            self.voice_handler = handler
        elif notification_type == NotificationType.PUSH:
            self.push_handler = handler
        elif notification_type == NotificationType.CHATOPS:
            self.chatops_handler = handler
        elif notification_type == NotificationType.EMAIL:
            self.email_handler = handler
        
        self.logger.info(f"Registered {handler.__class__.__name__} for {notification_type.value}")
    
    def dispatch_notification(self, notification_type: NotificationType, recipient: str, message: str, metadata: Optional[Dict[str, Any]] = None) -> NotificationResult:
        """
        Dispatch a single notification using the registered handler.
        
        Args:
            notification_type: Type of notification
            recipient: Recipient identifier
            message: Message content
            metadata: Additional metadata
            
        Returns:
            Notification result
        """
        handler = None
        if notification_type == NotificationType.SMS:
            handler = self.sms_handler
        elif notification_type == NotificationType.VOICE:
            handler = self.voice_handler
        elif notification_type == NotificationType.PUSH:
            handler = self.push_handler
        elif notification_type == NotificationType.CHATOPS:
            handler = self.chatops_handler
        elif notification_type == NotificationType.EMAIL:
            handler = self.email_handler
            
        if not handler:
            return NotificationResult(
                success=False,
                notification_type=notification_type,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                error=f"No handler registered for {notification_type.value}"
            )
            
        try:
            return handler.send(recipient, message, metadata)
        except Exception as e:
            self.logger.error(f"Notification failed: {e}")
            return NotificationResult(
                success=False,
                notification_type=notification_type,
                recipient=recipient,
                message=message,
                timestamp=datetime.now(),
                error=str(e)
            )

    def build_message(self, evaluation_result: Dict[str, Any]) -> str:
        """
        Build a notification message from an evaluation result.
        
        Args:
            evaluation_result: Result from rule engine evaluation
            
        Returns:
            Formatted message string
        """
        threat_type = evaluation_result["threat_type"]
        magnitude = evaluation_result["magnitude"]
        escalation_level = evaluation_result["escalation_level"]
        location = evaluation_result["location"]
        affected_count = len(evaluation_result["affected_entities"])
        
        message = (
            f"🚨 EMERGENCY ALERT [{escalation_level.upper()}]\n"
            f"Threat: {threat_type.upper()}\n"
            f"Magnitude: {magnitude:.1f}\n"
            f"Location: {location['lat']:.4f}, {location['lon']:.4f}\n"
            f"Affected entities: {affected_count}\n"
            f"Max risk score: {evaluation_result['max_risk_score']:.2f}\n"
            f"Action required: Contact emergency services immediately."
        )
        
        return message
    
    def dispatch_hotline_calls(self, evaluation_result: Dict[str, Any]) -> List[NotificationResult]:
        """
        Dispatch voice calls to hotlines.
        
        Args:
            evaluation_result: Result from rule engine evaluation
            
        Returns:
            List of notification results
        """
        results = []
        message = self.build_message(evaluation_result)
        
        for contact_number in evaluation_result["contact_numbers"]:
            # Try voice call with retries
            for attempt in range(self.retry_attempts):
                try:
                    result = self.voice_handler.send(
                        contact_number,
                        message,
                        metadata={
                            "event_id": evaluation_result["event_id"],
                            "attempt": attempt + 1
                        }
                    )
                    results.append(result)
                    if result.success:
                        break
                except Exception as e:
                    self.logger.error(f"Voice call failed (attempt {attempt + 1}): {e}")
                    if attempt == self.retry_attempts - 1:
                        results.append(NotificationResult(
                            success=False,
                            notification_type=NotificationType.VOICE,
                            recipient=contact_number,
                            message=message,
                            timestamp=datetime.now(),
                            error=str(e)
                        ))
        
        return results
    
    def dispatch_sms(self, evaluation_result: Dict[str, Any], recipients: List[str]) -> List[NotificationResult]:
        """
        Dispatch SMS notifications.
        
        Args:
            evaluation_result: Result from rule engine evaluation
            recipients: List of phone numbers
            
        Returns:
            List of notification results
        """
        results = []
        message = self.build_message(evaluation_result)
        
        for recipient in recipients:
            try:
                result = self.sms_handler.send(
                    recipient,
                    message,
                    metadata={"event_id": evaluation_result["event_id"]}
                )
                results.append(result)
            except Exception as e:
                self.logger.error(f"SMS failed: {e}")
                results.append(NotificationResult(
                    success=False,
                    notification_type=NotificationType.SMS,
                    recipient=recipient,
                    message=message,
                    timestamp=datetime.now(),
                    error=str(e)
                ))
        
        return results
    
    def dispatch_push(self, evaluation_result: Dict[str, Any], user_ids: List[str]) -> List[NotificationResult]:
        """
        Dispatch push notifications to mobile devices.
        
        Args:
            evaluation_result: Result from rule engine evaluation
            user_ids: List of user/device IDs
            
        Returns:
            List of notification results
        """
        results = []
        message = self.build_message(evaluation_result)
        
        for user_id in user_ids:
            try:
                result = self.push_handler.send(
                    user_id,
                    message,
                    metadata={
                        "event_id": evaluation_result["event_id"],
                        "action_buttons": ["Call 911", "Acknowledge"]
                    }
                )
                results.append(result)
            except Exception as e:
                self.logger.error(f"Push notification failed: {e}")
                results.append(NotificationResult(
                    success=False,
                    notification_type=NotificationType.PUSH,
                    recipient=user_id,
                    message=message,
                    timestamp=datetime.now(),
                    error=str(e)
                ))
        
        return results
    
    def dispatch_chatops(self, evaluation_result: Dict[str, Any], channel: str = "#emergency") -> NotificationResult:
        """
        Dispatch ChatOps notification (Slack, Teams, etc.).
        
        Args:
            evaluation_result: Result from rule engine evaluation
            channel: Channel or webhook URL
            
        Returns:
            Notification result
        """
        message = self.build_message(evaluation_result)
        
        # Add rich formatting for ChatOps
        rich_message = (
            f"{message}\n\n"
            f"**Affected Entities:**\n"
        )
        
        for entity in evaluation_result["affected_entities"][:5]:  # Limit to first 5
            rich_message += f"- {entity['name']} ({entity['type']}): Risk {entity['risk_score']:.2f}\n"
        
        try:
            result = self.chatops_handler.send(
                channel,
                rich_message,
                metadata={"event_id": evaluation_result["event_id"]}
            )
            return result
        except Exception as e:
            self.logger.error(f"ChatOps notification failed: {e}")
            return NotificationResult(
                success=False,
                notification_type=NotificationType.CHATOPS,
                recipient=channel,
                message=rich_message,
                timestamp=datetime.now(),
                error=str(e)
            )
    
    def dispatch_all(self, evaluation_result: Dict[str, Any]) -> Dict[str, List[NotificationResult]]:
        """
        Dispatch all notifications for an evaluation result.
        
        Args:
            evaluation_result: Result from rule engine evaluation
            
        Returns:
            Dictionary of notification results by type
        """
        results = {
            "voice": [],
            "sms": [],
            "push": [],
            "chatops": []
        }
        
        # Hotline voice calls
        results["voice"] = self.dispatch_hotline_calls(evaluation_result)
        
        # SMS to on-duty personnel
        on_duty_phones = [
            entity["contact_phone"]
            for entity in evaluation_result["affected_entities"]
            if entity.get("type") == "personnel" and entity.get("on_duty") and entity.get("contact_phone")
        ]
        if on_duty_phones:
            results["sms"] = self.dispatch_sms(evaluation_result, on_duty_phones)
        
        # Push to all affected personnel
        personnel_ids = [
            entity["id"]
            for entity in evaluation_result["affected_entities"]
            if entity.get("type") == "personnel"
        ]
        if personnel_ids:
            results["push"] = self.dispatch_push(evaluation_result, personnel_ids)
        
        # ChatOps notification
        chatops_result = self.dispatch_chatops(evaluation_result)
        results["chatops"] = [chatops_result]
        
        return results
