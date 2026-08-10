from unittest.mock import patch
from scripts.ingest import fetch_postings, flatten


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
