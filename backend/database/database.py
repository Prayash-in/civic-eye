import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator, Optional

from backend.config import DB_PATH, AnalysisStatus
from backend.models.report import Report, ReportCreate, ReportStatus

SCHEMA = """
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    image_path TEXT NOT NULL,
    description TEXT NOT NULL,
    category TEXT NOT NULL DEFAULT '',
    issue_type TEXT,
    severity TEXT,
    confidence REAL,
    explanation TEXT,
    latitude REAL,
    longitude REAL,
    status TEXT NOT NULL DEFAULT 'submitted',
    analysis_status TEXT NOT NULL DEFAULT 'pending',
    created_at TEXT NOT NULL
);
"""

# Nullable columns added by the Civic Intelligence phase. Existing rows keep
# working because every column is nullable and defaults to NULL.
ROUTING_COLUMNS = {
    "authority_name": "TEXT",
    "department": "TEXT",
    "routing_reason": "TEXT",
    "assembly_constituency_id": "TEXT",
    "assembly_constituency_name": "TEXT",
    "lok_sabha_constituency_id": "TEXT",
    "mla_name": "TEXT",
    "mla_party": "TEXT",
    "mp_name": "TEXT",
    "mp_party": "TEXT",
    "jurisdiction_status": "TEXT",
    "resolution_method": "TEXT",
    "notification_status": "TEXT",
    "notification_channel": "TEXT",
    "notification_sent_at": "TEXT",
}

NOTIFICATIONS_SCHEMA = """
CREATE TABLE IF NOT EXISTS notifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    report_id INTEGER NOT NULL REFERENCES reports(id),
    channel TEXT NOT NULL,
    recipient TEXT NOT NULL,
    status TEXT NOT NULL,
    error TEXT,
    created_at TEXT NOT NULL,
    sent_at TEXT
);
"""


@contextmanager
def _connection(db_path: Path) -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _migrate(conn: sqlite3.Connection) -> None:
    existing = {row["name"] for row in conn.execute("PRAGMA table_info(reports)")}
    for column, column_type in ROUTING_COLUMNS.items():
        if column not in existing:
            conn.execute(f"ALTER TABLE reports ADD COLUMN {column} {column_type}")
    conn.execute(NOTIFICATIONS_SCHEMA)


def init_db(db_path: Path = DB_PATH) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with _connection(db_path) as conn:
        conn.execute(SCHEMA)
        _migrate(conn)


def create_report(report: ReportCreate, db_path: Path = DB_PATH) -> Report:
    init_db(db_path)
    created_at = datetime.now(timezone.utc).isoformat()
    with _connection(db_path) as conn:
        cursor = conn.execute(
            """
            INSERT INTO reports (
                image_path,
                description,
                category,
                latitude,
                longitude,
                status,
                analysis_status,
                created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                report.image_path,
                report.description,
                report.category,
                report.latitude,
                report.longitude,
                ReportStatus.SUBMITTED.value,
                AnalysisStatus.PENDING.value,
                created_at,
            ),
        )
        report_id = cursor.lastrowid
    return get_report(report_id, db_path=db_path)


def get_report(report_id: int, db_path: Path = DB_PATH) -> Optional[Report]:
    init_db(db_path)
    with _connection(db_path) as conn:
        row = conn.execute(
            "SELECT * FROM reports WHERE id = ?",
            (report_id,),
        ).fetchone()
    return _row_to_report(row) if row is not None else None


def list_reports(
    db_path: Path = DB_PATH,
    issue_type: Optional[str] = None,
    severity: Optional[str] = None,
    status: Optional[str] = None,
    analysis_status: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
) -> list[Report]:
    init_db(db_path)
    clauses: list[str] = []
    params: list[object] = []

    if issue_type is not None:
        clauses.append("issue_type = ?")
        params.append(issue_type)
    if severity is not None:
        clauses.append("severity = ?")
        params.append(severity)
    if status is not None:
        clauses.append("status = ?")
        params.append(status)
    if analysis_status is not None:
        clauses.append("analysis_status = ?")
        params.append(analysis_status)

    where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
    sql = (
        "SELECT * FROM reports "
        f"{where} "
        "ORDER BY created_at DESC, id DESC "
        "LIMIT ? OFFSET ?"
    )
    params.extend([limit, offset])

    with _connection(db_path) as conn:
        rows = conn.execute(sql, params).fetchall()

    return [_row_to_report(row) for row in rows]


def update_analysis(
    report_id: int,
    issue_type: Optional[str],
    severity: Optional[str],
    confidence: Optional[float],
    explanation: Optional[str],
    analysis_status: str,
    db_path: Path = DB_PATH,
) -> Optional[Report]:
    init_db(db_path)
    with _connection(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE reports
            SET issue_type = ?,
                severity = ?,
                confidence = ?,
                explanation = ?,
                analysis_status = ?
            WHERE id = ?
            """,
            (
                issue_type,
                severity,
                confidence,
                explanation,
                analysis_status,
                report_id,
            ),
        )
        if cursor.rowcount == 0:
            return None
    return get_report(report_id, db_path=db_path)


def update_routing(report_id: int, routing: dict, db_path: Path = DB_PATH) -> Optional[Report]:
    """Persist jurisdiction + authority routing fields on a report."""
    init_db(db_path)
    assembly = routing.get("assembly_constituency") or {}
    lok_sabha = routing.get("lok_sabha_constituency") or {}
    mla = routing.get("mla") or {}
    mp = routing.get("mp") or {}
    authority = routing.get("authority") or {}

    with _connection(db_path) as conn:
        cursor = conn.execute(
            """
            UPDATE reports
            SET authority_name = ?,
                department = ?,
                routing_reason = ?,
                assembly_constituency_id = ?,
                assembly_constituency_name = ?,
                lok_sabha_constituency_id = ?,
                mla_name = ?,
                mla_party = ?,
                mp_name = ?,
                mp_party = ?,
                jurisdiction_status = ?,
                resolution_method = ?
            WHERE id = ?
            """,
            (
                authority.get("authority"),
                authority.get("department"),
                authority.get("routing_reason"),
                assembly.get("id"),
                assembly.get("name"),
                lok_sabha.get("id"),
                mla.get("name"),
                mla.get("party"),
                mp.get("name"),
                mp.get("party"),
                routing.get("jurisdiction_status"),
                routing.get("resolution_method"),
                report_id,
            ),
        )
        if cursor.rowcount == 0:
            return None
    return get_report(report_id, db_path=db_path)


def record_notification(
    report_id: int,
    channel: str,
    recipients: list[str],
    status: str,
    error: Optional[str],
    sent_at: Optional[str],
    db_path: Path = DB_PATH,
) -> None:
    """Store one row per recipient plus the roll-up status on the report."""
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with _connection(db_path) as conn:
        for recipient in recipients or ["(none)"]:
            conn.execute(
                """
                INSERT INTO notifications (
                    report_id, channel, recipient, status, error,
                    created_at, sent_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    report_id,
                    channel,
                    recipient,
                    status,
                    error,
                    now,
                    sent_at,
                ),
            )
        conn.execute(
            """
            UPDATE reports
            SET notification_status = ?,
                notification_channel = ?,
                notification_sent_at = ?
            WHERE id = ?
            """,
            (status, channel, sent_at, report_id),
        )


def get_notifications_for_report(
    report_id: int, db_path: Path = DB_PATH
) -> list[dict]:
    init_db(db_path)
    with _connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT id, report_id, channel, recipient, status, error,
                   created_at, sent_at
            FROM notifications
            WHERE report_id = ?
            ORDER BY id DESC
            """,
            (report_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def get_recent_notifications(limit: int = 10, db_path: Path = DB_PATH) -> list[dict]:
    """Latest notification events joined with their report for the dashboard."""
    init_db(db_path)
    with _connection(db_path) as conn:
        rows = conn.execute(
            """
            SELECT n.id, n.report_id, n.channel, n.recipient, n.status,
                   n.error, n.created_at, n.sent_at,
                   r.issue_type, r.severity,
                   r.authority_name, r.department
            FROM notifications n
            JOIN reports r ON r.id = n.report_id
            ORDER BY n.id DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_report(report_id: int, db_path: Path = DB_PATH) -> bool:
    init_db(db_path)
    with _connection(db_path) as conn:
        conn.execute(
            "DELETE FROM notifications WHERE report_id = ?",
            (report_id,),
        )
        cursor = conn.execute(
            "DELETE FROM reports WHERE id = ?",
            (report_id,),
        )
        return cursor.rowcount > 0


REPORT_ROUTING_FIELDS = [
    "authority_name",
    "department",
    "routing_reason",
    "assembly_constituency_id",
    "assembly_constituency_name",
    "lok_sabha_constituency_id",
    "mla_name",
    "mla_party",
    "mp_name",
    "mp_party",
    "jurisdiction_status",
    "resolution_method",
    "notification_status",
    "notification_channel",
    "notification_sent_at",
]


def _row_to_report(row: sqlite3.Row) -> Report:
    return Report(
        id=row["id"],
        image_path=row["image_path"],
        description=row["description"],
        category=row["category"],
        issue_type=row["issue_type"],
        severity=row["severity"],
        confidence=row["confidence"],
        explanation=row["explanation"],
        latitude=row["latitude"],
        longitude=row["longitude"],
        status=ReportStatus(row["status"]),
        analysis_status=AnalysisStatus(row["analysis_status"]),
        created_at=datetime.fromisoformat(row["created_at"]),
        **{
            field: row[field]
            for field in REPORT_ROUTING_FIELDS
        },
    )
