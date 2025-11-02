import pytest
import requests
import time
from concurrent.futures import ThreadPoolExecutor, as_completed

BASE_URL = "https://hacker-news.firebaseio.com/v0"

@pytest.fixture(scope="module")
def response():
    re = requests.Session()
    re.headers.update({"Accept": "application/json"})
    return re


#negative test
def test_invalid_returns_401(response):
    """ No authentication should return 401"""
    res = response.get(f"{BASE_URL}/thisfiledoesnotexists.json")
    assert res.status_code == 401, "Expected 401 for invalid"


#test a invalid id
@pytest.mark.parametrize("item_id", ["asdasas", -1, 0])
def test_invalid_item_id_returns_null(response, item_id):
    """ Invalid item IDs should return null or {}."""
    res = response.get(f"{BASE_URL}/item/{item_id}.json")
    assert res.status_code == 200, "Invalid ID should still return 200 (null body)"
    data = res.json()
    assert data in (None, {}, []), f"Expected null or empty JSON for invalid ID, got {data}"


#test a item was missing or been deleted
def test_deleted_or_missing_item(response):
    """ Deleted or missing items should have 'deleted' or be null."""
    # Try fetching a known deleted item (use an obviously large ID)
    res = response.get(f"{BASE_URL}/item/99.json")
    assert res.status_code == 200
    data = res.json()
    if data is None:
        pytest.skip("Item not found — expected for very large IDs")
    else:
        # Some deleted items return {"deleted": true}
        assert "deleted" in data or "dead" in data or "title" in data, \
            "Response should contain item data or deleted flag"


#format 
def test_content_type_is_json(response):
    """ API should always return JSON content type."""
    res = response.get(f"{BASE_URL}/topstories.json")
    assert res.status_code == 200
    assert "application/json" in res.headers.get("Content-Type", ""), \
        f"Unexpected Content-Type: {res.headers.get('Content-Type')}"


#Empty list
def test_empty_list_handling(response):
    """ Handle empty list response gracefully."""
    res = response.get(f"{BASE_URL}/topstories.json")
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list), "Response must be a list"
    # Simulate empty list edge case
    if not data:
        pytest.skip("Received empty list — valid but rare condition")

# --- Edge cases for data ---

def test_top_stories_have_unique_ids(response):
    """ Ensure no duplicated story IDs."""
    res = response.get(f"{BASE_URL}/topstories.json")
    assert res.status_code == 200
    ids = res.json()
    assert isinstance(ids, list)
    assert len(ids) == len(set(ids)), "Duplicate IDs found in top stories"


def test_valid_item_type(response):
    """ Ensure only valid item types appear in responses."""
    valid_types = {"story", "comment", "poll", "pollopt", "job"}
    top_ids = response.get(f"{BASE_URL}/topstories.json").json()[:10]
    for sid in top_ids:
        item = response.get(f"{BASE_URL}/item/{sid}.json").json()
        assert item["type"] in valid_types, f"Invalid item type: {item['type']}"


def test_story_can_have_no_comments(response):
    """ Stories without 'kids' should be handled gracefully."""
    story_id = response.get(f"{BASE_URL}/topstories.json").json()[0]
    story = response.get(f"{BASE_URL}/item/{story_id}.json").json()
    if "kids" not in story:
        pytest.skip(f"Story {story_id} has no comments — expected valid edge case")
    else:
        assert isinstance(story["kids"], list)


def test_deleted_or_dead_items_handling(response):
    """ Deleted or dead items should be detected correctly."""
    # Try fetching a large ID that may not exist or is deleted
    item = response.get(f"{BASE_URL}/item/99.json").json()
    if item is None:
        pytest.skip("No such item — valid missing edge case")
    if "deleted" in item or "dead" in item:
        assert isinstance(item.get("deleted", False), bool)
        assert isinstance(item.get("dead", False), bool)

# --- Rate Limiting & Load ---

def test_frequent_requests_stability(response):
    """ Sequential requests should not degrade or fail."""
    durations = []
    for _ in range(10):  # Make 10 quick requests
        start = time.perf_counter()
        res = response.get(f"{BASE_URL}/topstories.json")
        elapsed = (time.perf_counter() - start) * 1000
        durations.append(elapsed)

        assert res.status_code == 200, "Expected 200 OK for repeated requests"
        assert res.elapsed.total_seconds() < 2, "Response took too long"

    avg_ms = sum(durations) / len(durations)
    assert avg_ms < 500, "Average response time should remain performant (<500ms)"


def test_concurrent_requests_stability(response):
    """ API should handle multiple parallel requests."""
    urls = [f"{BASE_URL}/topstories.json" for _ in range(5)]
    results = []

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(response.get, url) for url in urls]
        for future in as_completed(futures):
            res = future.result()
            results.append(res)

    statuses = [r.status_code for r in results]
    assert all(code == 200 for code in statuses), f"Some concurrent requests failed: {statuses}"


def test_rate_limit_behavior(response):
    # Intentionally make several rapid requests
    responses = []
    for _ in range(15):
        res = response.get(f"{BASE_URL}/topstories.json")
        responses.append(res)
        time.sleep(0.1)  # Small delay between requests

    status_codes = [r.status_code for r in responses]

    if 429 in status_codes:
        assert status_codes.count(429) < len(status_codes) / 2, "Too many rate limit hits"


def test_consistent_performance_under_load(response):
    """ Response time should stay stable under burst load."""
    times = []
    for _ in range(5):
        start = time.perf_counter()
        res = response.get(f"{BASE_URL}/topstories.json")
        elapsed_ms = (time.perf_counter() - start) * 1000
        times.append(elapsed_ms)
        assert res.status_code == 200

    variation = max(times) - min(times)
    assert variation < 500, "Performance fluctuated too much under load"


def test_no_server_errors_under_load(response):
    """ No 5xx errors during a small load burst."""
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(response.get, f"{BASE_URL}/topstories.json") for _ in range(10)]
        results = [f.result() for f in as_completed(futures)]

    for res in results:
        assert res.status_code < 500, f"Server error detected: {res.status_code}"


