import os

import psycopg
import pytest

from app.models import (
    ComparisonAssessmentPayload,
    ComparisonCoursePayload,
    ComparisonSyncPayload,
)
from app.persistence.comparison_sqlite_store import ComparisonSqliteStore

pytestmark = pytest.mark.skipif(
    not os.getenv("DATABASE_URL"),
    reason="DATABASE_URL no configurado — se omiten tests de PostgreSQL",
)


def _payload(name: str, claim_code: str | None = None, sync_token: str | None = None):
    return ComparisonSyncPayload(
        participant_name=name,
        claim_code=claim_code,
        sync_token=sync_token,
        courses=[
            ComparisonCoursePayload(
                canonical_course_key="icc1001",
                course_code="ICC1001",
                course_title="Programacion",
                term_code="202510",
                term_label="Primer Semestre - 2025",
                section="1",
                status="En curso",
                current_grade=6.1,
                final_grade=None,
                comparison_grade=6.1,
                assessments=[
                    ComparisonAssessmentPayload(
                        assessment_name="Control 1",
                        canonical_assessment_key="control-1",
                        weight=25.0,
                        grade=6.1,
                        grade_text="6.1",
                        must_pass=False,
                        order_index=1,
                    )
                ],
            )
        ],
    )


@pytest.fixture()
def store():
    database_url = os.environ["DATABASE_URL"]
    s = ComparisonSqliteStore(database_url)
    yield s
    with psycopg.connect(database_url) as conn:
        conn.execute(
            "TRUNCATE participant_assessments, participant_course_attempts, "
            "sync_runs, courses, claim_invites, participants RESTART IDENTITY CASCADE"
        )


def test_claim_and_replace_snapshot_issues_sync_token(store):
    store.sync_claim_invites({"Martin A.": "claim-martin"})

    identity = store.claim_and_replace_snapshot(
        display_name="Martin A.",
        claim_code="claim-martin",
        courses=_payload("Martin A.").courses,
    )

    assert identity.display_name == "Martin A."
    assert identity.sync_token
    assert store.load_dashboard_rows()


def test_claim_requires_matching_preassigned_code(store):
    store.sync_claim_invites({"Martin A.": "claim-martin"})

    issued_token = store.claim_identity(
        display_name="Martin A.",
        claim_code="claim-martin",
    )

    assert issued_token


def test_revoked_invite_cannot_be_claimed_after_resync(store):
    store.sync_claim_invites({"Martin A.": "claim-martin"})

    store.sync_claim_invites({})

    try:
        store.claim_identity(display_name="Martin A.", claim_code="claim-martin")
    except PermissionError as error:
        assert str(error) == "claim_invite_invalid"
    else:
        raise AssertionError("Expected PermissionError")


def test_resync_updates_course_metadata_for_existing_canonical_key(store):
    store.sync_claim_invites({"Martin A.": "claim-martin"})
    issued_token = store.claim_identity(
        display_name="Martin A.",
        claim_code="claim-martin",
    )

    store.replace_participant_snapshot(_payload("Martin A.", sync_token=issued_token))
    store.replace_participant_snapshot(
        ComparisonSyncPayload(
            participant_name="Martin A.",
            claim_code=None,
            sync_token=issued_token,
            courses=[
                ComparisonCoursePayload(
                    canonical_course_key="icc1001",
                    course_code="ICC-1001A",
                    course_title="Programacion Actualizada",
                    term_code="202520",
                    term_label="Segundo Semestre - 2025",
                    section="2",
                    status="Cerrado",
                    current_grade=6.3,
                    final_grade=6.3,
                    comparison_grade=6.3,
                    assessments=[],
                )
            ],
        )
    )

    rows = store.load_dashboard_rows()
    assert len(rows) == 1
    assert rows[0]["course_title"] == "Programacion Actualizada"


def test_replace_snapshot_rejects_wrong_token(store):
    store.sync_claim_invites({"Martin A.": "claim-martin"})
    identity = store.claim_and_replace_snapshot(
        display_name="Martin A.",
        claim_code="claim-martin",
        courses=_payload("Martin A.").courses,
    )

    bad_payload = _payload("Martin A.", sync_token="wrong-token")

    try:
        store.replace_participant_snapshot(bad_payload)
    except PermissionError as error:
        assert str(error) == "sync_token_invalid"
    else:
        raise AssertionError("Expected PermissionError")

    good_payload = _payload("Martin A.", sync_token=identity.sync_token)
    store.replace_participant_snapshot(good_payload)
    assert (
        store.load_identity("Martin A.", identity.sync_token).display_name
        == "Martin A."
    )


def test_replace_snapshot_requires_sync_token(store):
    try:
        store.replace_participant_snapshot(_payload("Martin A."))
    except PermissionError as error:
        assert str(error) == "sync_token_required"
    else:
        raise AssertionError("Expected PermissionError")
