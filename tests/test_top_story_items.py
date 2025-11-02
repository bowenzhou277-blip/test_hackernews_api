import requests
import pytest

BASE_URL = "https://hacker-news.firebaseio.com/v0"


@pytest.fixture(scope="module")
def top_story_id():
    """Fetch the first top story ID."""
    top_stories_url = f"{BASE_URL}/topstories.json"
    response = requests.get(top_stories_url, timeout=2)
    assert response.status_code == 200, "Failed to retrieve top stories"
    
    story_ids = response.json()
    assert isinstance(story_ids, list), "Expected a list of IDs"
    assert len(story_ids) > 0, "Top stories list is empty"
    return story_ids[0]


def test_get_top_story_details(top_story_id):
    """Retrieve and validate the current top story using the Items API."""
    item_url = f"{BASE_URL}/item/{top_story_id}.json"
    response = requests.get(item_url, timeout=2)

    # --- Validate response ---
    assert response.status_code == 200, "Failed to fetch top story details"
    story = response.json()
    assert story is not None, "Story response is empty"

    # --- Validate schema ---
    required_fields = ["id", "title", "by", "time", "type"]
    for field in required_fields:
        assert field in story, f"Missing field: {field}"

    # --- Validate content ---
    assert story["id"] == top_story_id, "Story ID mismatch"
    assert story["type"] == "story", f"Unexpected item type: {story['type']}"
    assert isinstance(story["title"], str) and len(story["title"]) > 0, "Invalid title"
    assert isinstance(story["by"], str), "Invalid author"
    assert isinstance(story["time"], int), "Invalid timestamp"


def test_top_story_response_time(top_story_id):
    """Ensure the top story is retrieved quickly."""
    item_url = f"{BASE_URL}/item/{top_story_id}.json"
    response = requests.get(item_url, timeout=2)
    assert response.elapsed.total_seconds() < 0.5
    , "Top story response is too slow"
