from src.analysis.dead_reg_detector import DeadRegulationDetector


def test_ai_none_has_no_ai_fields():
    detector = DeadRegulationDetector(ai_client=None)
    result = detector.analyze_document(
        {
            "id": "doc-1",
            "title": "Test",
            "full_text": "Обычный текст без старых терминов.",
        }
    )

    assert "ai_used" not in result
    assert "ai_summary" not in result
    assert "ai_error" not in result
