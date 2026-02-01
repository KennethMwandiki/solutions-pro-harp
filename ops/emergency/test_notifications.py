"""
Comprehensive Notification System Test Script
Tests Email, SMS, Push (FCM), and ChatOps (Slack/Teams) notifications.
"""
from ops.emergency.notifications import (
    NotificationDispatcher,
    NotificationType, 
)
from ops.emergency.data_models import EscalationLevel
from ops.emergency.notifications import (
    MockEmailHandler,
    MockSMSHandler,
    MockPushHandler,
    MockChatOpsHandler
)

def test_notification_service():
    """Run comprehensive test of notification service."""
    print("=" * 60)
    print("Pro-Harp Notification Service Test")
    print("=" * 60)
    
    # Initialize notification dispatcher with mock handlers
    dispatcher = NotificationDispatcher()
    
    # Register mock handlers for all channels
    dispatcher.register_handler(NotificationType.EMAIL, MockEmailHandler())
    dispatcher.register_handler(NotificationType.SMS, MockSMSHandler())
    dispatcher.register_handler(NotificationType.PUSH, MockPushHandler())
    dispatcher.register_handler(NotificationType.CHATOPS, MockChatOpsHandler())
    
    print("\n[INFO] Registered all notification handlers")
    
    # Test scenario: Critical orbital anomaly detected
    test_alert = {
        "alert_id": "TEST-ORBITAL-001",
        "severity": EscalationLevel.CRITICAL,
        "title": "Orbital Anomaly Detected",
        "message": "Satellite VTH-101 has deviated from expected trajectory. Immediate action required.",
        "metadata": {
            "satellite_id": "VTH-101",
            "confidence": 0.95,
            "coordinates": {"lat": 28.5, "lon": -80.6}
        }
    }
    
    print(f"\n[TEST] Simulating alert: {test_alert['alert_id']}")
    print(f"[TEST] Severity: {test_alert['severity'].value}")
    print(f"[TEST] Message: {test_alert['message']}")
    
    # Test 1: Email Notification
    print("\n--- Test 1: Email Notification ---")
    email_result = dispatcher.dispatch_notification(
        notification_type=NotificationType.EMAIL,
        recipient="security-ops@proharp.com",
        message=test_alert['message'],
        metadata={"subject": test_alert['title'], **test_alert['metadata']}
    )
    print(f"[RESULT] Email: {'SUCCESS' if email_result.success else 'FAILED'}")
    
    # Test 2: SMS Notification
    print("\n--- Test 2: SMS Notification ---")
    sms_result = dispatcher.dispatch_notification(
        notification_type=NotificationType.SMS,
        recipient="+15551234567",
        message=f"[CRITICAL] {test_alert['title']}: {test_alert['message'][:100]}",
        metadata=test_alert['metadata']
    )
    print(f"[RESULT] SMS: {'SUCCESS' if sms_result.success else 'FAILED'}")
    
    # Test 3: Push Notification (Firebase Cloud Messaging)
    print("\n--- Test 3: Push Notification (FCM) ---")
    push_result = dispatcher.dispatch_notification(
        notification_type=NotificationType.PUSH,
        recipient="device_token_12345",
        message=test_alert['message'],
        metadata={
            "title": test_alert['title'],
            "priority": "high",
            **test_alert['metadata']
        }
    )
    print(f"[RESULT] Push: {'SUCCESS' if push_result.success else 'FAILED'}")
    
    # Test 4: ChatOps Notification (Slack/Teams)
    print("\n--- Test 4: ChatOps Notification (Slack/Teams) ---")
    chatops_result = dispatcher.dispatch_notification(
        notification_type=NotificationType.CHATOPS,
        recipient="#security-alerts",
        message=f"[CRITICAL] **{test_alert['title']}**\\n{test_alert['message']}\\n\\nSatellite: {test_alert['metadata']['satellite_id']} | Confidence: {test_alert['metadata']['confidence']*100}%",
        metadata=test_alert['metadata']
    )
    print(f"[RESULT] ChatOps: {'SUCCESS' if chatops_result.success else 'FAILED'}")
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    results = [email_result, sms_result, push_result, chatops_result]
    success_count = sum(1 for r in results if r.success)
    print(f"[SUMMARY] Passed: {success_count}/{len(results)}")
    print(f"[SUMMARY] All notification channels operational: {'YES' if success_count == len(results) else 'NO'}")
    
    # Check log files
    print("\n--- Log Files Generated ---")
    from pathlib import Path
    log_dir = Path("notification_logs")
    if log_dir.exists():
        for log_file in log_dir.glob("*.jsonl"):
            size = log_file.stat().st_size
            print(f"[LOG] {log_file.name} ({size} bytes)")
    
    print("\n[INFO] Test complete. Check notification_logs/ for detailed logs.")
    return success_count == len(results)

if __name__ == "__main__":
    import sys
    success = test_notification_service()
    sys.exit(0 if success else 1)
