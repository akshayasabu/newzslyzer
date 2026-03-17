from app import app, get_live_articles
import json

with app.app_context():
    print("Fetching Sports News (Baseline)...")
    articles, title = get_live_articles("Sports")
    print(f"Fetch completed. Found {len(articles)} articles.")
    for a in articles[:3]:
        print(f"- {a['title']}")
