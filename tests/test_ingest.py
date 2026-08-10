from unittest.mock import patch, MagicMock
from scripts.ingest import fetch_postings, flatten, run_ingest


def test_flatten_maps_fields_correctly():
    """Ensure flatten maps nested fields into dataframe columns correctly."""
    postings = [
        {
            'id': '123',
            'title': 'Analytics Engineer',
            'company': {'display_name': 'Acme Corp'},
            'location': {'display_name': 'Boston, MA'},
            'salary_min': 90000,
            'salary_max': 110000,
            'description': 'A great job',
            'created': '2026-08-01T00:00:00Z',
            'category': {'label': 'IT Jobs'},
            'redirect_url': 'https://example.com/job/123',
        }
    ]
    df = flatten(postings, loaded_at='2026-08-07T12:00:00')

    assert len(df) == 1
    assert df.iloc[0]['posting_id'] == '123'
    assert df.iloc[0]['company'] == 'Acme Corp'
    assert df.iloc[0]['location'] == 'Boston, MA'
    assert df.iloc[0]['loaded_at'] == '2026-08-07T12:00:00'


def test_flatten_handles_missing_nested_fields():
    """Ensure flatten handles missing nested company/location data gracefully."""
    postings = [{'id': '456', 'title': 'SQL Developer'}]
    df = flatten(postings, loaded_at='2026-08-07T12:00:00')

    assert df.iloc[0]['company'] is None
    assert df.iloc[0]['location'] is None


def test_flatten_empty_returns_empty_dataframe():
    """Ensure flatten returns an empty DataFrame when no postings are provided."""
    df = flatten([], loaded_at='2026-08-07T12:00:00')

    assert df.empty


def test_fetch_posting_single_page():
    """Test fetching a single page of results."""
    mock_response = {
        'results': [
            {'id': '1', 'title': 'Job 1'},
            {'id': '2', 'title': 'Job 2'},
        ],
        'pagecount': 1,
    }

    with patch('scripts.ingest.requests.get') as mock_get:
        mock_get.return_value.json.return_value = mock_response
        mock_get.return_value.raise_for_status.return_value = None

        results = fetch_postings('analytics engineer')

        assert len(results) == 2
        assert results[0]['id'] == '1'
        assert results[1]['id'] == '2'
        mock_get.assert_called_once()


def test_fetch_postings_multiple_pages():
    """Test pagination across multiple pages"""
    page1 = {'results': [{'id': '1', 'title': 'Job 1'}], 'pagecount': 2}
    page2 = {'results': [{'id': '2', 'title': 'Job 2'}], 'pagecount': 2}

    with patch('scripts.ingest.requests.get') as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.side_effect = [page1, page2]

        results = fetch_postings('data engineer')

        assert len(results) == 2
        assert mock_get.call_count == 2


def test_fetch_postings_timeout():
    """Test timeout error handling"""
    import requests

    with patch('scripts.ingest.requests.get') as mock_get:
        mock_get.side_effect = requests.exceptions.Timeout('Timeout')

        results = fetch_postings('sql developer')

        assert results == []


def test_fetch_postings_invalid_json():
    """Test JSON parse error handling"""
    with patch('scripts.ingest.requests.get') as mock_get:
        mock_get.return_value.raise_for_status.return_value = None
        mock_get.return_value.json.side_effect = ValueError('Invalid JSON')

        results = fetch_postings('analytics engineer')

        assert results == []


def test_run_ingest_missing_api_creds(monkeypatch):
    """Test that run_ingest exits if API credentials missing"""
    monkeypatch.setenv('ADZUNA_APP_ID', '')
    monkeypatch.setenv('ADZUNA_APP_KEY', '')

    results = run_ingest()

    assert results is None


def test_run_ingest_no_postings(monkeypatch):
    """Test that run_ingest exits if no postings fetched"""
    monkeypatch.setenv('ADZUNA_APP_ID', 'test')
    monkeypatch.setenv('ADZUNA_APP_KEY', 'test')

    with patch('scripts.ingest.fetch_postings', return_value=[]):
        from scripts.ingest import run_ingest

        result = run_ingest()

        assert result is None


def test_run_ingest_full_flow(monkeypatch):
    """Test full run_ingest flow with mocked Snowflake"""
    monkeypatch.setenv('ADZUNA_APP_ID', 'test')
    monkeypatch.setenv('ADZUNA_APP_KEY', 'test')
    monkeypatch.setenv('SNOWFLAKE_ACCOUNT', 'test')
    monkeypatch.setenv('SNOWFLAKE_USER', 'test')
    monkeypatch.setenv('SNOWFLAKE_PASSWORD', 'test')
    monkeypatch.setenv('SNOWFLAKE_WAREHOUSE', 'test')
    monkeypatch.setenv('SNOWFLAKE_DATABASE', 'test')
    monkeypatch.setenv('SNOWFLAKE_SCHEMA', 'test')
    with (
        patch('scripts.ingest.fetch_postings') as mock_fetch,
        patch('scripts.ingest.snowflake.connector.connect') as mock_conn,
        patch('scripts.ingest.write_pandas') as mock_write,
    ):
        mock_fetch.return_value = [{'id': '1', 'title': 'Job 1'}]
        mock_cursor = MagicMock()
        mock_conn.return_value.cursor.return_value = mock_cursor
        mock_write.return_value = (True, None, 1, None)

        from scripts.ingest import run_ingest

        run_ingest()

        mock_conn.assert_called_once()
        mock_write.assert_called_once()
        mock_cursor.execute.assert_any_call('TRUNCATE TABLE postings_staging')
