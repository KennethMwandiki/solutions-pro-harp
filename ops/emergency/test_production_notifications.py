"""
Test script for production notification handlers.
Tests real implementations with fallback to mock mode if credentials not configured.
"""
import sys
import os
from pathlib import Path

# Ensure we can import from the root and emergency directory
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
sys.path.insert(0, str(Path(__file__).parent))

from ops.emergency.production_notifications import (
    SMTPEmailHandler,
    TwilioSMSHandler,
    FirebasePushHandler,
    SlackWebhookHandler,
    TeamsWebhookHandler
)
from ops.emergency.notifications import NotificationDispatcher, NotificationType
from ops.emergency.data_models import EscalationLevel

def test_production_handlers():
    """Test all production notification handlers."""
    print("=" * 60)
    print("Pro-Harp Production Notification Handlers Test")
    print("=" * 60)
    
    # Initialize dispatcher
    dispatcher = NotificationDispatcher()
    
    # Register production handlers
    print("\n[INFO] Registering production handlers...")
    email_handler = SMTPEmailHandler()
    sms_handler = TwilioSMSHandler()
    push_handler = FirebasePushHandler()
    slack_handler = SlackWebhookHandler()
    teams_handler = TeamsWebhookHandler()
    
    dispatcher.register_handler(NotificationType.EMAIL, email_handler)
    dispatcher.register_handler(NotificationType.SMS, sms_handler)
    dispatcher.register_handler(NotificationType.PUSH, push_handler)
    dispatcher.register_handler(NotificationType.CHATOPS, slack_handler)  # Primary ChatOps
    
    # Check handler status
    print("\n--- Handler Configuration Status ---")
    print(f"Email (SMTP): {'ENABLED' if email_handler.enabled else 'MOCK MODE - No credentials'}")
    print(f"SMS (Twilio): {'ENABLED' if sms_handler.enabled else 'MOCK MODE - No credentials'}")
    print(f"Push (Firebase): {'ENABLED' if push_handler.enabled else 'MOCK MODE - No credentials'}")
    print(f"Slack Webhook: {'ENABLED' if slack_handler.enabled else 'MOCK MODE - No webhook URL'}")
    print(f"Teams Webhook: {'ENABLED' if teams_handler.enabled else 'MOCK MODE - No webhook URL'}")
    
    # Test alert scenario
    test_alert = {
        "alert_id": "PROD-TEST-001",
        "severity": EscalationLevel.HIGH,
        "title": "Production Handler Test",
        "message": "Testing production notification handlers with real API integrations. This is a test alert from Pro-Harp.",
        "metadata": {
            "facility": "TEST-FACILITY",
            "confidence": 1.0,
            "test_mode": True
        }
    }
    
    print(f"\n[TEST] Simulating alert: {test_alert['alert_id']}")
    print(f"[TEST] Message: {test_alert['message']}")
    
    results = []
    
    # Test 1: Email
    print("\n--- Test 1: Email (SMTP) ---")
    email_result = dispatcher.dispatch_notification(
        notification_type=NotificationType.EMAIL,
        recipient="test@example.com",
        message=test_alert['message'],
        metadata={"subject": test_alert['title'], **test_alert['metadata']}
    )
    results.append(("Email", email_result))
    print(f"[RESULT] {'SUCCESS' if email_result.success else 'FAILED'} - {email_result.error or 'Sent successfully'}")
    
    # Test 2: SMS
    print("\n--- Test 2: SMS (Twilio) ---")
    sms_result = dispatcher.dispatch_notification(
        notification_type=NotificationType.SMS,
        recipient="+15551234567",
        message=f"[CRITICAL] {test_alert['title']}: {test_alert['message'][:100]}",
        metadata=test_alert['metadata']
    )
    results.append(("SMS", sms_result))
    print(f"[RESULT] {'SUCCESS' if sms_result.success else 'FAILED'} - {sms_result.error or 'Sent successfully'}")
    
    # Test 3: Push (Firebase)
    print("\n--- Test 3: Push Notification (Firebase) ---")
    push_result = dispatcher.dispatch_notification(
        notification_type=NotificationType.PUSH,
        recipient="test_device_token_12345",
        message=test_alert['message'],
        metadata={
            "title": test_alert['title'],
            "priority": "high",
            **test_alert['metadata']
        }
    )
    results.append(("Push", push_result))
    print(f"[RESULT] {'SUCCESS' if push_result.success else 'FAILED'} - {push_result.error or 'Sent successfully'}")
    
    # Test 4: Slack
    print("\n--- Test 4: ChatOps (Slack) ---")
    slack_result = dispatcher.dispatch_notification(
        notification_type=NotificationType.CHATOPS,
        recipient="#security-alerts",
        message=f"[CRITICAL] **{test_alert['title']}**\n{test_alert['message']}",
        metadata=test_alert['metadata']
    )
    results.append(("Slack", slack_result))
    print(f"[RESULT] {'SUCCESS' if slack_result.success else 'FAILED'} - {slack_result.error or 'Sent successfully'}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    success_count = sum(1 for _, r in results if r.success)
    print(f"[SUMMARY] Passed: {success_count}/{len(results)}")
    
    # Production readiness
    enabled_count = sum(1 for h in [email_handler, sms_handler, push_handler, slack_handler] if hasattr(h, 'enabled') and h.enabled)
    print(f"[SUMMARY] Production handlers enabled: {enabled_count}/4")
    
    if enabled_count == 0:
        print("\n[NOTICE] All handlers in MOCK MODE. Configure credentials in .env to activate:")
        print("  - SMTP_USERNAME, SMTP_PASSWORD (Email)")
        print("  - TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN (SMS)")
        print("  - FIREBASE_SERVICE_ACCOUNT_PATH (Push)")
        print("  - SLACK_WEBHOOK_URL (Slack)")
    elif enabled_count < 4:
        print(f"\n[NOTICE] {4 - enabled_count} handler(s) still in MOCK MODE. Check .env configuration.")
    else:
        print("\n[SUCCESS] All production handlers are ENABLED and operational!")
    
    # Check log files
    print("\n--- Notification Logs ---")
    log_dir = Path("notification_logs")
    if log_dir.exists():
        for log_file in sorted(log_dir.glob("*.jsonl")):
            size = log_file.stat().st_size
            print(f"[LOG] {log_file.name} ({size} bytes)")
    else:
        print("[INFO] No logs directory found (will be created on first notification)")
    
    print("\n[INFO] Test complete!")
    return success_count == len(results)

if __name__ == "__main__":
    try:
        from dotenv import load_dotenv
        load_dotenv()
        print("[INFO] Loaded environment variables from .env")
    except ImportError:
        print("[WARNING] python-dotenv not installed. Using system environment variables.")
    
    success = test_production_handlers()
    sys.exit(0 if success else 1)
