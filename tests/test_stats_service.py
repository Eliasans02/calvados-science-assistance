from pathlib import Path

from src.metrics.stats_service import StatsEvent, StatsService


def test_stats_service_tracks_and_persists(tmp_path: Path):
    stats_path = tmp_path / "stats.json"
    service = StatsService(stats_path=stats_path)
    try:
        service.track_document(StatsEvent(document_type="pdf", source="upload", ai_result="skipped"))
        service.track_document(StatsEvent(document_type="docx", source="adilet", ai_result="success"))
        service.track_document(StatsEvent(document_type="pdf", source="adilet", ai_result="failed"))
        service.flush()

        snapshot = service.get_stats()
        assert snapshot["total_processed_documents"] == 3
        assert snapshot["document_types"]["pdf"] == 2
        assert snapshot["document_types"]["docx"] == 1
        assert snapshot["document_sources"]["adilet"] == 2
        assert snapshot["ai_results"]["success"] == 1
        assert snapshot["ai_results"]["failed"] == 1
        assert snapshot["ai_results"]["skipped"] == 1
        assert snapshot["analysis_results"]["success"] == 3
        assert snapshot["analysis_results"]["failed"] == 0
        assert len(snapshot["recent_analyses"]) == 3
        assert stats_path.exists()
    finally:
        service.stop()
