from __future__ import annotations

from collections import defaultdict


def _select_option(
    options: list[dict[str, str]], requested_value: str | None
) -> str | None:
    values = {option["value"] for option in options}
    if requested_value in values:
        return requested_value
    if not options:
        return None
    return options[0]["value"]


def _average(values: list[float | None]) -> float | None:
    valid = [value for value in values if value is not None]
    if not valid:
        return None
    return round(sum(valid) / len(valid), 2)


def _rank_with_points(entries: dict[str, list[float | None]]) -> list[dict]:
    ranking = [
        {
            "display_name": display_name,
            "average": _average(grades),
            "wins": 0,
            "podiums": 0,
            "points": 0,
        }
        for display_name, grades in entries.items()
    ]
    ranking.sort(
        key=lambda item: (item["average"] is not None, item["average"] or -1),
        reverse=True,
    )
    leader_average = ranking[0]["average"] if ranking else None
    for index, row in enumerate(ranking[:3]):
        row["podiums"] += 1
        row["points"] += [3, 2, 1][index]
        if index == 0:
            row["wins"] += 1
    for row in ranking:
        row["gap_to_leader"] = (
            0.0
            if leader_average is None or row["average"] is None
            else round(leader_average - row["average"], 2)
        )
    return ranking


def build_comparison_dashboard_context(
    rows: list[dict],
    *,
    highlight_participant: str | None = None,
    selected_course: str | None = None,
    selected_semester: str | None = None,
    selected_assessment: str | None = None,
) -> dict:
    # course+semester keyed — used for course panel and semester course breakdown
    by_course_sem: defaultdict[tuple[str, str, str], list[float | None]] = defaultdict(list)
    # semester keyed — used for semester ranking
    by_semester: defaultdict[tuple[str, str], list[float | None]] = defaultdict(list)
    # historical (all semesters) — used for historical ranking
    by_historical: defaultdict[str, list[float | None]] = defaultdict(list)
    # assessment keyed with semester — used for course panel assessment breakdown
    by_assessment_sem: defaultdict[tuple[str, str, str, str], list[float | None]] = defaultdict(list)

    assessment_order: dict[tuple[str, str, str], tuple[int, str]] = {}
    course_labels: dict[str, str] = {}
    semester_labels: dict[str, str] = {}

    # Pass 1: collect assessment grades and metadata per (display_name, course_key, term_code)
    attempt_assess_grades: defaultdict[tuple[str, str, str], list[float]] = defaultdict(list)
    attempt_course_grade: dict[tuple[str, str, str], float | None] = {}

    for row in rows:
        display_name = row["display_name"]
        course_key = row["canonical_course_key"]
        term_code = row["term_code"]
        term_label = row["term_label"]
        attempt_key = (display_name, course_key, term_code)

        if attempt_key not in attempt_course_grade:
            attempt_course_grade[attempt_key] = row.get("comparison_grade")

        if row.get("assessment_name") and row.get("assessment_grade") is not None:
            assessment_name = row["assessment_name"]
            attempt_assess_grades[attempt_key].append(row["assessment_grade"])
            by_assessment_sem[(course_key, term_code, assessment_name, display_name)].append(
                row["assessment_grade"]
            )
            order_index = row.get("assessment_order_index")
            sort_key = (
                order_index if isinstance(order_index, int) else 10**9,
                assessment_name,
            )
            existing = assessment_order.get((course_key, term_code, assessment_name))
            if existing is None or sort_key < existing:
                assessment_order[(course_key, term_code, assessment_name)] = sort_key

        course_labels[course_key] = row["course_title"]
        semester_labels[term_code] = term_label

    # Pass 2: build aggregation dicts using effective grade
    # (course-level grade if available, else simple average of graded assessments)
    seen_attempts: set[tuple[str, str, str]] = set()
    for row in rows:
        display_name = row["display_name"]
        course_key = row["canonical_course_key"]
        term_code = row["term_code"]
        attempt_key = (display_name, course_key, term_code)
        if attempt_key in seen_attempts:
            continue
        seen_attempts.add(attempt_key)

        grade = attempt_course_grade[attempt_key]
        if grade is None:
            assess = attempt_assess_grades[attempt_key]
            if assess:
                grade = round(sum(assess) / len(assess), 2)

        by_course_sem[(course_key, term_code, display_name)].append(grade)
        by_semester[(term_code, display_name)].append(grade)
        by_historical[display_name].append(grade)

    course_options = [
        {"value": key, "label": label}
        for key, label in sorted(
            course_labels.items(), key=lambda item: (item[1], item[0])
        )
    ]
    semester_options = [
        {"value": key, "label": label}
        for key, label in sorted(
            semester_labels.items(), key=lambda item: item[0], reverse=True
        )
    ]
    selected_semester = _select_option(semester_options, selected_semester)

    semester_course_keys = {
        ck for (ck, tc, _dn) in by_course_sem if tc == selected_semester
    }
    course_options_for_semester = [
        o for o in course_options if o["value"] in semester_course_keys
    ]
    selected_course = _select_option(course_options_for_semester, selected_course)

    # ── Course panel: ranking filtered by course + semester ──────────────
    course_ranking = _rank_with_points(
        {
            display_name: grades
            for (course_key, term_code, display_name), grades in by_course_sem.items()
            if course_key == selected_course and term_code == selected_semester
        }
    )

    # ── Course panel: all assessments for selected course + semester ──────
    assessment_names_for_course = sorted(
        {
            assessment_name
            for (ck, tc, assessment_name, _dn) in by_assessment_sem
            if ck == selected_course and tc == selected_semester
        },
        key=lambda name: assessment_order.get(
            (selected_course, selected_semester, name), (10**9, name)
        ),
    )
    all_assessment_rankings = [
        {
            "assessment_name": aname,
            "ranking": _rank_with_points(
                {
                    display_name: grades
                    for (ck, tc, an, display_name), grades in by_assessment_sem.items()
                    if ck == selected_course and tc == selected_semester and an == aname
                }
            ),
        }
        for aname in assessment_names_for_course
    ]

    # ── Semester panel: courses breakdown (each course in the semester) ───
    sem_course_entries: defaultdict[str, dict[str, list[float | None]]] = defaultdict(
        lambda: defaultdict(list)
    )
    for (course_key, term_code, display_name), grades in by_course_sem.items():
        if term_code == selected_semester:
            sem_course_entries[course_key][display_name].extend(grades)

    semester_courses = [
        {
            "course_key": ck,
            "course_title": course_labels.get(ck, ck),
            "ranking": _rank_with_points(
                {dn: grades for dn, grades in participants.items()}
            ),
        }
        for ck, participants in sorted(
            sem_course_entries.items(),
            key=lambda item: course_labels.get(item[0], item[0]),
        )
    ]

    # ── Semester ranking ─────────────────────────────────────────────────
    semester_ranking = _rank_with_points(
        {
            display_name: grades
            for (term_code, display_name), grades in by_semester.items()
            if term_code == selected_semester
        }
    )

    # ── Historical ranking ───────────────────────────────────────────────
    historical_ranking = _rank_with_points(dict(by_historical))
    selected_row = next(
        (
            row
            for row in historical_ranking
            if row["display_name"] == highlight_participant
        ),
        None,
    )
    group_average = _average(
        [row["average"] for row in historical_ranking if row["average"] is not None]
    )

    return {
        "summary": {
            "leaders": [row["display_name"] for row in historical_ranking[:3]],
            "participants": len(by_historical),
            "group_average": group_average,
            "leader_points": historical_ranking[0]["points"] if historical_ranking else 0,
            "selected_participant": selected_row,
        },
        "tabs": {
            "course": {
                "selected": selected_course,
                "options": course_options_for_semester,
                "ranking": course_ranking,
                "all_assessment_rankings": all_assessment_rankings,
            },
            "semester": {
                "selected": selected_semester,
                "options": semester_options,
                "ranking": semester_ranking,
                "courses": semester_courses,
            },
            "historical": {
                "ranking": historical_ranking,
            },
        },
    }
