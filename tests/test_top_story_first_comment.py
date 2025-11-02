import requests
import pytest

BASE_URL = "https://hacker-news.firebaseio.com/v0"


@pytest.fixture(scope="module")
def top_story():
    """Fetch the top story object."""
    top_stories_url = f"{BASE_URL}/topstories.json"
    response = requests.get(top_stories_url, timeout=2)
    assert response.status_code == 200, "Failed to retrieve top stories"
    story_ids = response.json()
    assert isinstance(story_ids, list) and len(story_ids) > 0, "Top stories list is empty"

    top_story_id = story_ids[0]
    story_url = f"{BASE_URL}/item/{top_story_id}.json"
    story_response = requests.get(story_url, timeout=2)
    assert story_response.status_code == 200, "Failed to retrieve top story"
    story = story_response.json()
    return story
    

def test_retrieve_first_comment(top_story):
    
    """Verify that the top story has at least one comment."""
    assert "kids" in top_story, "Top story has no comments"
    assert isinstance(top_story["kids"], list), "'kids' should be a list"
    assert len(top_story["kids"]) > 0, "Top story has an empty comment list"

    """Retrieve the first comment from the top story using the Items API."""
    comment_id = top_story["kids"][0]
    comment_url = f"{BASE_URL}/item/{comment_id}.json"
    comment_response = requests.get(comment_url, timeout=2)
    assert comment_response.status_code == 200, "Failed to retrieve comment"

    comment = comment_response.json()
    assert comment is not None, "Comment response is empty"

    # --- Validate core fields ---
    required_fields = ["id", "by", "text", "time", "type"]
    for field in required_fields:
        assert field in comment, f"Missing field '{field}' in comment"

    # --- Validate content ---
    assert comment["type"] == "comment", f"Expected type 'comment', got {comment['type']}"
    assert isinstance(comment["by"], str), "Invalid author type"
    assert isinstance(comment["time"], int), "Invalid timestamp"
    assert isinstance(comment["text"], str) and len(comment["text"]) > 0, "Comment text is empty"


def test_first_comment_response_time(top_story):
    """Ensure comment retrieval is fast."""
    comment_id = top_story["kids"][0]
    comment_url = f"{BASE_URL}/item/{comment_id}.json"
    response = requests.get(comment_url, timeout=2)
    assert response.elapsed.total_seconds() < 0.5, "Comment response too slow"
