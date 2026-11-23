from src.utils.logger import _filter_lid_logs


def test_api_key_query_parameter_is_redacted():
    record = {"message": "Open https://example.test/qr?API_KEY=super-secret&x=1"}

    assert _filter_lid_logs(record) is True
    assert record["message"] == "Open https://example.test/qr?API_KEY=***&x=1"


def test_lid_migration_noise_is_filtered():
    record = {"message": "Migrated to LID encryption"}

    assert _filter_lid_logs(record) is False
