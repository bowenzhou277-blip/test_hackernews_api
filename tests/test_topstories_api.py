import requests
import pytest

BASE_URL = "https://hacker-news.firebaseio.com/v0"

@pytest.fixture(scope="module")
def top_stories_response():
    """Fixture to call the Top Stories API once per test module."""
    url = f"{BASE_URL}/topstories.json"
    response = requests.get(url, timeout=2)
    return response

def test_retrieve_top_stories(top_stories_response):
    """ Retrieving top stories with the Top Stories API"""
    assert top_stories_response.status_code == 200, "Expected 200 OK"
    data = top_stories_response.json()

    # Basic response validation
    assert isinstance(data, list), "Response should be a list"
    assert len(data) > 0, "Should return at least one story ID"
    assert isinstance(data[0], int), "Story IDs should be integers"

    print(f"Retrieved {len(data)} top stories, first ID: {data[0]}")



def test_topstories_response_time(top_stories_response):
    """Check that the response is timely (under 500 ms)."""
    assert top_stories_response.elapsed.total_seconds() < 0.5, \
        "API response took too long."



def test_topstories_first_story_is_valid(top_stories_response):
    """Fetch the first story to confirm it exists and has required fields."""
    story_ids = top_stories_response.json()
    first_story_id = story_ids[0]
    item_url = f"{BASE_URL}/item/{first_story_id}.json"
    story_response = requests.get(item_url, timeout=2)

    assert story_response.status_code == 200, "Failed to fetch story details"
    story_data = story_response.json()

    required_fields = ["id", "type", "title", "by", "time"]
    for field in required_fields:
        assert field in story_data, f"Missing field '{field}' in story data"
    assert story_data["type"] == "story", f"Unexpected type: {story_data['type']}"
