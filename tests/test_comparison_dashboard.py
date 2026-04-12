from app.services.comparison_dashboard import build_comparison_dashboard_context


def test_builds_rankings_and_stable_defaults():
    rows = [
        {
            "display_name": "Martin A.",
            "canonical_course_key": "PHY101",
            "course_title": "Fisica I",
            "term_code": "202410",
            "term_label": "Segundo Semestre - 2024",
            "comparison_grade": 4.0,
            "assessment_name": "Laboratorio",
            "assessment_grade": 4.5,
            "assessment_order_index": 2,
        },
        {
            "display_name": "Martin A.",
            "canonical_course_key": "MAT101",
            "course_title": "Calculo I",
            "term_code": "202510",
            "term_label": "Primer Semestre - 2025",
            "comparison_grade": 6.0,
            "assessment_name": "Solemne 2",
            "assessment_grade": 5.8,
            "assessment_order_index": 2,
        },
        {
            "display_name": "Martin A.",
            "canonical_course_key": "MAT101",
            "course_title": "Calculo I",
            "term_code": "202510",
            "term_label": "Primer Semestre - 2025",
            "comparison_grade": 6.0,
            "assessment_name": "Solemne 1",
            "assessment_grade": 6.2,
            "assessment_order_index": 1,
        },
        {
            "display_name": "Camila R.",
            "canonical_course_key": "MAT101",
            "course_title": "Calculo I",
            "term_code": "202510",
            "term_label": "Primer Semestre - 2025",
            "comparison_grade": 5.0,
            "assessment_name": "Solemne 1",
            "assessment_grade": 5.0,
            "assessment_order_index": 1,
        },
    ]

    context = build_comparison_dashboard_context(
        rows, highlight_participant="Martin A."
    )

    assert context["tabs"]["course"]["selected"] == "MAT101"
    assert context["tabs"]["course"]["selected_assessment"] == "Solemne 1"
    assert context["tabs"]["semester"]["selected"] == "202510"
    assert context["tabs"]["course"]["ranking"][0]["display_name"] == "Martin A."
    assert (
        context["tabs"]["course"]["assessment_ranking"][0]["display_name"]
        == "Martin A."
    )
    assert context["summary"]["selected_participant"]["display_name"] == "Martin A."
