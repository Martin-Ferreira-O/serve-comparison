from __future__ import annotations

import hashlib
import secrets
from contextlib import contextmanager
from typing import Iterator

import psycopg
from psycopg.rows import dict_row

from app.models import ComparisonIdentity, ComparisonSyncPayload


def _hash_token(raw: str) -> str:
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


class ComparisonSqliteStore:
    def __init__(self, database_url: str):
        self._database_url = database_url
        self._ensure_schema()

    @contextmanager
    def _connect(self) -> Iterator[psycopg.Connection]:
        with psycopg.connect(self._database_url, row_factory=dict_row) as connection:
            yield connection

    def _ensure_schema(self) -> None:
        statements = [
            """
            CREATE TABLE IF NOT EXISTS participants (
                id SERIAL PRIMARY KEY,
                display_name TEXT NOT NULL UNIQUE,
                sync_token_hash TEXT NOT NULL,
                claimed_at TEXT NOT NULL,
                latest_synced_at TEXT,
                is_active INTEGER NOT NULL DEFAULT 1
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS claim_invites (
                id SERIAL PRIMARY KEY,
                display_name TEXT NOT NULL UNIQUE,
                claim_code_hash TEXT NOT NULL,
                claimed_at TEXT,
                participant_id INTEGER
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS sync_runs (
                id SERIAL PRIMARY KEY,
                participant_id INTEGER NOT NULL,
                received_at TEXT NOT NULL,
                status TEXT NOT NULL,
                payload_version TEXT NOT NULL,
                courses_count INTEGER NOT NULL,
                assessments_count INTEGER NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS courses (
                id SERIAL PRIMARY KEY,
                canonical_course_key TEXT NOT NULL UNIQUE,
                course_code TEXT NOT NULL,
                course_title TEXT NOT NULL
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS participant_course_attempts (
                id SERIAL PRIMARY KEY,
                participant_id INTEGER NOT NULL,
                course_id INTEGER NOT NULL,
                term_code TEXT NOT NULL,
                term_label TEXT NOT NULL,
                section TEXT,
                status TEXT NOT NULL,
                current_grade REAL,
                final_grade REAL,
                comparison_grade REAL,
                components_available INTEGER NOT NULL DEFAULT 0
            )
            """,
            """
            CREATE TABLE IF NOT EXISTS participant_assessments (
                id SERIAL PRIMARY KEY,
                course_attempt_id INTEGER NOT NULL,
                canonical_assessment_key TEXT NOT NULL,
                assessment_name TEXT NOT NULL,
                weight REAL NOT NULL,
                grade REAL,
                grade_text TEXT NOT NULL,
                must_pass INTEGER NOT NULL,
                order_index INTEGER NOT NULL
            )
            """,
        ]
        with self._connect() as connection:
            for stmt in statements:
                connection.execute(stmt)

    def sync_claim_invites(self, invites: dict[str, str]) -> None:
        with self._connect() as connection:
            if invites:
                placeholders = ", ".join("%s" for _ in invites)
                connection.execute(
                    f"DELETE FROM claim_invites WHERE claimed_at IS NULL AND display_name NOT IN ({placeholders})",
                    tuple(invites),
                )
            else:
                connection.execute("DELETE FROM claim_invites WHERE claimed_at IS NULL")

            for display_name, claim_code in invites.items():
                connection.execute(
                    """
                    INSERT INTO claim_invites (display_name, claim_code_hash, claimed_at, participant_id)
                    VALUES (%s, %s, NULL, NULL)
                    ON CONFLICT(display_name) DO UPDATE SET claim_code_hash = excluded.claim_code_hash
                    WHERE claim_invites.claimed_at IS NULL
                    """,
                    (display_name, _hash_token(claim_code)),
                )

    def add_claim_invite(self, display_name: str, claim_code: str) -> None:
        with self._connect() as connection:
            row = connection.execute(
                """
                INSERT INTO claim_invites (display_name, claim_code_hash, claimed_at, participant_id)
                VALUES (%s, %s, NULL, NULL)
                ON CONFLICT(display_name) DO UPDATE SET claim_code_hash = excluded.claim_code_hash
                WHERE claim_invites.claimed_at IS NULL
                RETURNING id
                """,
                (display_name, _hash_token(claim_code)),
            ).fetchone()
        if row is None:
            raise PermissionError("claim_invite_already_claimed")

    def claim_identity(self, *, display_name: str, claim_code: str) -> str:
        sync_token = secrets.token_urlsafe(24)
        claim_code_hash = _hash_token(claim_code)
        sync_token_hash = _hash_token(sync_token)
        with self._connect() as connection:
            invite = connection.execute(
                "SELECT id, claimed_at FROM claim_invites WHERE display_name = %s AND claim_code_hash = %s",
                (display_name, claim_code_hash),
            ).fetchone()
            if invite is None or invite["claimed_at"] is not None:
                raise PermissionError("claim_invite_invalid")
            try:
                cursor = connection.execute(
                    "INSERT INTO participants (display_name, sync_token_hash, claimed_at) VALUES (%s, %s, NOW()) RETURNING id",
                    (display_name, sync_token_hash),
                )
            except psycopg.errors.UniqueViolation as error:
                raise PermissionError("claim_invite_invalid") from error
            participant_id = cursor.fetchone()["id"]
            connection.execute(
                "UPDATE claim_invites SET claimed_at = NOW(), participant_id = %s WHERE id = %s",
                (participant_id, invite["id"]),
            )
        return sync_token

    def claim_and_replace_snapshot(
        self,
        *,
        display_name: str,
        claim_code: str,
        courses: list,
    ) -> ComparisonIdentity:
        sync_token = secrets.token_urlsafe(24)
        claim_code_hash = _hash_token(claim_code)
        sync_token_hash = _hash_token(sync_token)
        payload = ComparisonSyncPayload(
            participant_name=display_name,
            claim_code=None,
            sync_token=sync_token,
            courses=courses,
        )
        with self._connect() as connection:
            invite = connection.execute(
                "SELECT id, claimed_at FROM claim_invites WHERE display_name = %s AND claim_code_hash = %s",
                (display_name, claim_code_hash),
            ).fetchone()
            if invite is None or invite["claimed_at"] is not None:
                raise PermissionError("claim_invite_invalid")
            try:
                cursor = connection.execute(
                    "INSERT INTO participants (display_name, sync_token_hash, claimed_at) VALUES (%s, %s, NOW()) RETURNING id",
                    (display_name, sync_token_hash),
                )
            except psycopg.errors.UniqueViolation as error:
                raise PermissionError("claim_invite_invalid") from error
            participant_id = cursor.fetchone()["id"]
            connection.execute(
                "UPDATE claim_invites SET claimed_at = NOW(), participant_id = %s WHERE id = %s",
                (participant_id, invite["id"]),
            )
            self._replace_snapshot(connection, participant_id, payload)
            row = connection.execute(
                "SELECT latest_synced_at FROM participants WHERE id = %s",
                (participant_id,),
            ).fetchone()
        return ComparisonIdentity(
            display_name=display_name,
            sync_token=sync_token,
            last_synced_at=None
            if row["latest_synced_at"] is None
            else str(row["latest_synced_at"]),
        )

    def _participant_id_for_token(self, display_name: str, sync_token: str) -> int:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT id FROM participants WHERE display_name = %s AND sync_token_hash = %s",
                (display_name, _hash_token(sync_token)),
            ).fetchone()
        if row is None:
            raise PermissionError("sync_token_invalid")
        return int(row["id"])

    def load_identity(self, display_name: str, sync_token: str) -> ComparisonIdentity:
        with self._connect() as connection:
            row = connection.execute(
                "SELECT display_name, latest_synced_at FROM participants WHERE display_name = %s AND sync_token_hash = %s",
                (display_name, _hash_token(sync_token)),
            ).fetchone()
        if row is None:
            raise PermissionError("sync_token_invalid")
        return ComparisonIdentity(
            display_name=str(row["display_name"]),
            sync_token=sync_token,
            last_synced_at=None
            if row["latest_synced_at"] is None
            else str(row["latest_synced_at"]),
        )

    def replace_participant_snapshot(self, payload: ComparisonSyncPayload) -> None:
        if not payload.sync_token:
            raise PermissionError("sync_token_required")

        participant_id = self._participant_id_for_token(
            payload.participant_name,
            payload.sync_token,
        )

        with self._connect() as connection:
            self._replace_snapshot(connection, participant_id, payload)

    def _replace_snapshot(
        self,
        connection: psycopg.Connection,
        participant_id: int,
        payload: ComparisonSyncPayload,
    ) -> None:
        attempt_ids = connection.execute(
            "SELECT id FROM participant_course_attempts WHERE participant_id = %s",
            (participant_id,),
        ).fetchall()
        for attempt_row in attempt_ids:
            connection.execute(
                "DELETE FROM participant_assessments WHERE course_attempt_id = %s",
                (attempt_row["id"],),
            )
        connection.execute(
            "DELETE FROM participant_course_attempts WHERE participant_id = %s",
            (participant_id,),
        )

        assessments_count = 0
        for course in payload.courses:
            connection.execute(
                """
                INSERT INTO courses (canonical_course_key, course_code, course_title)
                VALUES (%s, %s, %s)
                ON CONFLICT(canonical_course_key) DO UPDATE SET
                    course_code = excluded.course_code,
                    course_title = excluded.course_title
                """,
                (course.canonical_course_key, course.course_code, course.course_title),
            )
            course_row = connection.execute(
                "SELECT id FROM courses WHERE canonical_course_key = %s",
                (course.canonical_course_key,),
            ).fetchone()
            attempt_cursor = connection.execute(
                """
                INSERT INTO participant_course_attempts (
                    participant_id, course_id, term_code, term_label, section, status, current_grade, final_grade, comparison_grade, components_available
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    participant_id,
                    course_row["id"],
                    course.term_code,
                    course.term_label,
                    course.section,
                    course.status,
                    course.current_grade,
                    course.final_grade,
                    course.comparison_grade,
                    1 if course.assessments else 0,
                ),
            )
            course_attempt_id = attempt_cursor.fetchone()["id"]
            for assessment in course.assessments:
                assessments_count += 1
                connection.execute(
                    """
                    INSERT INTO participant_assessments (
                        course_attempt_id, canonical_assessment_key, assessment_name, weight, grade, grade_text, must_pass, order_index
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        course_attempt_id,
                        assessment.canonical_assessment_key,
                        assessment.assessment_name,
                        assessment.weight,
                        assessment.grade,
                        assessment.grade_text,
                        1 if assessment.must_pass else 0,
                        assessment.order_index,
                    ),
                )

        connection.execute(
            "UPDATE participants SET latest_synced_at = NOW() WHERE id = %s",
            (participant_id,),
        )
        connection.execute(
            "INSERT INTO sync_runs (participant_id, received_at, status, payload_version, courses_count, assessments_count) VALUES (%s, NOW(), 'ok', 'v1', %s, %s)",
            (participant_id, len(payload.courses), assessments_count),
        )

    def load_dashboard_rows(self) -> list[dict]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT
                    participants.display_name,
                    courses.canonical_course_key,
                    courses.course_title,
                    participant_course_attempts.term_code,
                    participant_course_attempts.term_label,
                    participant_course_attempts.comparison_grade,
                    participant_assessments.assessment_name,
                    participant_assessments.grade AS assessment_grade,
                    participant_assessments.order_index AS assessment_order_index
                FROM participant_course_attempts
                JOIN participants ON participants.id = participant_course_attempts.participant_id
                JOIN courses ON courses.id = participant_course_attempts.course_id
                LEFT JOIN participant_assessments ON participant_assessments.course_attempt_id = participant_course_attempts.id
                WHERE participants.is_active = 1
                ORDER BY participants.display_name, participant_course_attempts.term_code DESC
                """
            ).fetchall()
        return list(rows)
