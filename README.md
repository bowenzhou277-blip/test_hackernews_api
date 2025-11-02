# test_hackernews_api test suites

Automated acceptance tests for the [Hacker News public API](https://github.com/HackerNews/API).

## Tests
-  Top Stories API returns valid story IDs
-  Items API returns valid story details
-  Retrieve a top story’s first comment
-  Some other edge cases 

## ▶️ Run Locally  (require Python3.10 or above)
```bash

clone this repo 
python3 -m venv venv
source venv/bin/activate    
pip install -r requirements.txt
pytest


