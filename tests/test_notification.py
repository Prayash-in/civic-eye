import smtplib
from unittest.mock import MagicMock, patch

from backend.models.report import Report
from backend.services import notification_service
from backend.services.notification_service import (
    build_notification,
    send_authority_notification,
)

passed = 0
failed = 0


def report(name: str, ok: bool) -> None:
    global passed, failed
    if ok:
        passed += 1
        print(f"PASS  {name}")
    else:
        failed += 1
        print(f"FAIL  {name}")


def make_report(report_id=42, issue_type="pothole", severity="high"):
    return Report(
        id=report_id,
        image_path="data/uploads/test.jpg",
        description='Pothole with <script>alert("x")</script> injection & quotes',
        category="road",
        issue_type=issue_type,
        severity=severity,
        confidence=0.91,
        explanation="Stub",
        latitude=26.17,
        longitude=91.665,
        created_at=__import__("datetime").datetime(
            2026, 8, 22, 10, 0, 0
        ),
        authority_name=None,
    )


AUTHORITY_INFO = {
    "authority": "Guwahati Municipal Corporation",
    "department": "Roads & Infrastructure",
    "routing_reason": "Road surface damage is handled by the municipal roads wing.",
}

JURISDICTION = {
    "jurisdiction_status": "resolved",
    "assembly_constituency": {"id": "AS-037", "name": "Jalukbari"},
    "lok_sabha_constituency": {"id": "GUWAHATI", "name": "Guwahati"},
    "mla": {"name": "Himanta Biswa Sarma", "party": "Bharatiya Janata Party"},
    "mp": {"name": "Bijuli Kalita Medhi", "party": "Bharatiya Janata Party"},
}


print("=" * 60)
print("NOTIFICATION SERVICE TESTS")
print("=" * 60)

# ----------------------------------------------------------
# 1. Not configured: no recipients -> explicit not_configured
# ----------------------------------------------------------
with patch.object(notification_service, "demo_recipients", return_value=[]):
    result = send_authority_notification(make_report(), AUTHORITY_INFO, JURISDICTION)

report(
    "no recipients: not_configured (never raises)",
    result["status"] == "not_configured" and "recipients" in result,
)

# ----------------------------------------------------------
# 2. Not configured: recipients but no SMTP host
# ----------------------------------------------------------
with (
    patch.object(
        notification_service,
        "demo_recipients",
        return_value=["demo1@example.com"],
    ),
    patch.object(notification_service, "SMTP_HOST", None),
):
    result = send_authority_notification(make_report(), AUTHORITY_INFO, JURISDICTION)

report(
    "no SMTP host: not_configured",
    result["status"] == "not_configured" and "SMTP" in (result.get("error") or ""),
)

# ----------------------------------------------------------
# 3. Disabled via NOTIFICATION_ENABLED=false -> skipped
# ----------------------------------------------------------
with patch.object(notification_service, "NOTIFICATION_ENABLED", False):
    result = send_authority_notification(make_report(), AUTHORITY_INFO, JURISDICTION)

report("disabled flag: skipped", result["status"] == "skipped")

# ----------------------------------------------------------
# 4. Successful send goes ONLY to the two demo mailboxes
# ----------------------------------------------------------
sent_messages = []


class StubSMTP:
    def __init__(self, host, port, timeout=None):
        self.host = host

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def starttls(self):
        pass

    def login(self, user, password):
        pass

    def sendmail(self, from_addr, to_addrs, msg):
        sent_messages.append((from_addr, tuple(to_addrs), msg))


with (
    patch.object(
        notification_service,
        "demo_recipients",
        return_value=["demo1@example.com", "demo2@example.com"],
    ),
    patch.object(notification_service, "SMTP_HOST", "smtp.test.local"),
    patch.object(notification_service, "SMTP_PORT", 587),
    patch.object(notification_service, "SMTP_FROM_EMAIL", "civic@test.local"),
    patch("backend.services.notification_service.smtplib.SMTP", StubSMTP),
):
    result = send_authority_notification(make_report(), AUTHORITY_INFO, JURISDICTION)

report(
    "configured: status sent with timestamp",
    result["status"] == "sent"
    and bool(result.get("sent_at"))
    and result.get("channel") == "email",
)
report(
    "recipients are exactly the demo mailboxes",
    sorted(result.get("recipients", []))
    == ["demo1@example.com", "demo2@example.com"],
)
report(
    "one message delivered covering both demo recipients",
    len(sent_messages) == 1 and len(sent_messages[0][1]) == 2,
)
if sent_messages:
    import email as email_lib

    mime_msg = email_lib.message_from_string(sent_messages[0][2])
    decoded_parts = []
    for part in mime_msg.walk():
        if not part.is_multipart():
            payload = part.get_payload(decode=True) or b""
            decoded_parts.append(payload.decode("utf-8", "replace"))
    full_body = "\n".join(decoded_parts)
    report(
        "message labeled as DEMO notification",
        "DEMO NOTIFICATION" in full_body,
    )
else:
    report("message labeled as DEMO notification", False)

# ----------------------------------------------------------
# 5. SMTP failure -> failed status with sanitized error
# ----------------------------------------------------------


class ExplodingSMTP:
    def __init__(self, *args, **kwargs):
        raise smtplib.SMTPAuthenticationError(535, b"secret-password-leak")


with (
    patch.object(
        notification_service,
        "demo_recipients",
        return_value=["demo1@example.com"],
    ),
    patch.object(notification_service, "SMTP_HOST", "smtp.test.local"),
    patch("backend.services.notification_service.smtplib.SMTP", ExplodingSMTP),
):
    try:
        result = send_authority_notification(
            make_report(), AUTHORITY_INFO, JURISDICTION
        )
        raised = False
    except Exception:
        raised = True
        result = {}

report("smtp failure: no exception escapes", not raised)
report(
    "smtp failure: status failed + sanitized error",
    result.get("status") == "failed"
    and "secret-password" not in str(result.get("error")),
)

# ----------------------------------------------------------
# 6. Content building: escaping + required fields
# ----------------------------------------------------------
content = build_notification(make_report(), AUTHORITY_INFO, JURISDICTION)
html_body = content["html_body"]

report(
    "subject includes severity label + CIV id",
    "CIV-00042" in content["subject"] and "High Priority" in content["subject"],
)
report(
    "HTML escapes script injection",
    "<script>" not in html_body and "&lt;script&gt;" in html_body,
)
report(
    "HTML contains department + MLA + MP",
    "Roads &amp; Infrastructure" in html_body
    and "Himanta Biswa Sarma" in html_body
    and "Bijuli Kalita Medhi" in html_body,
)
report(
    "plain text lists assembly constituency",
    "Jalukbari" in content["text_body"]
    and "Assembly Constituency: Jalukbari" in content["text_body"],
)
report(
    "bodies disclose demo-only nature",
    content["text_body"].count("demo") + html_body.lower().count("demo") >= 2,
)

print("=" * 60)
print(f"Passed: {passed}/{passed + failed}")
assert failed == 0, f"{failed} notification tests failed"
