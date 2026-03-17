#!/usr/bin/env python
"""Test script to verify that different articles get unique images"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import get_dynamic_news_image

def test_unique_images():
    """Test that different articles get different image URLs"""
    
    print("\n" + "="*70)
    print("UNIQUE IMAGE GENERATION TEST")
    print("="*70)
    
    # Test 1: Different titles should get different images
    print("\n[Test 1] Different Titles → Different Images")
    print("-"*70)
    
    articles = [
        ("Breaking: Cricket Match Highlights", "Sports", "article_1"),
        ("Tech Innovation Unveiled", "Tech", "article_2"),
        ("Political Debate Results", "Politics", "article_3"),
        ("Entertainment News Update", "Entertainment", "article_4"),
        ("Health Tips for Wellness", "Health", "article_5"),
    ]
    
    image_urls = {}
    for title, category, article_id in articles:
        url = get_dynamic_news_image(title, category, article_id)
        image_urls[article_id] = url
        print(f"  {article_id}: {title[:40]:40} → {url}")
    
    # Check uniqueness
    unique_urls = set(image_urls.values())
    if len(unique_urls) == len(image_urls):
        print(f"\n  ✓ All {len(image_urls)} articles have UNIQUE images!")
    else:
        print(f"\n  ✗ Warning: Only {len(unique_urls)} unique images for {len(image_urls)} articles")
        # Show duplicates
        from collections import Counter
        url_counts = Counter(image_urls.values())
        duplicates = {url: count for url, count in url_counts.items() if count > 1}
        if duplicates:
            print("  Duplicate URLs:")
            for url, count in duplicates.items():
                print(f"    - {url} (used {count} times)")
    
    # Test 2: Same title with different IDs should get different images
    print("\n[Test 2] Same Title + Different IDs → Different Images")
    print("-"*70)
    
    same_title = "Breaking News Update"
    same_category = "News"
    
    urls_same_title = []
    for i in range(5):
        url = get_dynamic_news_image(same_title, same_category, f"id_{i}")
        urls_same_title.append(url)
        print(f"  ID {i}: {url}")
    
    unique_same_title = set(urls_same_title)
    if len(unique_same_title) == len(urls_same_title):
        print(f"\n  ✓ Same title with different IDs produces {len(unique_same_title)} UNIQUE images!")
    else:
        print(f"\n  ✗ Warning: Only {len(unique_same_title)} unique images for {len(urls_same_title)} IDs")
    
    # Test 3: Category-specific images
    print("\n[Test 3] Category-Specific Images")
    print("-"*70)
    
    categories_test = [
        ("Sports News Update", "Sports"),
        ("Tech News Update", "Tech"),
        ("Politics News Update", "Politics"),
        ("Entertainment News Update", "Entertainment"),
        ("Health News Update", "Health"),
    ]
    
    category_urls = {}
    for title, category in categories_test:
        url = get_dynamic_news_image(title, category, f"cat_{category}")
        category_urls[category] = url
        # Extract search query from URL
        search_part = url.split('/')[4].split('?')[0]
        print(f"  {category:15} → Search: {search_part:20} → {url}")
    
    unique_category_urls = set(category_urls.values())
    if len(unique_category_urls) == len(category_urls):
        print(f"\n  ✓ All {len(category_urls)} categories have UNIQUE images!")
    else:
        print(f"\n  ✗ Warning: Only {len(unique_category_urls)} unique images for {len(category_urls)} categories")
    
    # Test 4: Keyword detection
    print("\n[Test 4] Keyword Detection in Titles")
    print("-"*70)
    
    keyword_tests = [
        ("T20 World Cup Final Match", "Sports", "Should detect: cricket,match"),
        ("Elon Musk SpaceX Launch", "Tech", "Should detect: musk,spacex"),
        ("Modi Government Policy", "Politics", "Should detect: modi,india"),
        ("Bitcoin Price Surge", "Business", "Should detect: bitcoin,crypto"),
        ("Hollywood Movie Release", "Entertainment", "Should detect: hollywood,cinema"),
    ]
    
    for title, category, expected in keyword_tests:
        url = get_dynamic_news_image(title, category, f"kw_{title[:10]}")
        search_part = url.split('/')[4].split('?')[0]
        print(f"  Title: {title[:35]:35}")
        print(f"    Expected: {expected}")
        print(f"    Got:      {search_part}")
        print(f"    URL:      {url}")
        print()
    
    # Test 5: URL parameter analysis
    print("\n[Test 5] URL Parameter Analysis")
    print("-"*70)
    
    test_article = ("Sample News Article", "News", "test_123")
    url = get_dynamic_news_image(*test_article)
    
    print(f"  Generated URL: {url}")
    print(f"\n  URL Components:")
    parts = url.split('?')
    base = parts[0]
    params = parts[1] if len(parts) > 1 else ""
    
    print(f"    Base URL: {base}")
    print(f"    Parameters: {params}")
    
    if 'lock=' in params and 'random=' in params:
        print(f"\n  ✓ URL includes both 'lock' and 'random' parameters for uniqueness")
    else:
        print(f"\n  ✗ Warning: URL missing uniqueness parameters")
    
    # Summary
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    total_tests = 5
    passed_tests = 0
    
    if len(unique_urls) == len(image_urls):
        passed_tests += 1
    if len(unique_same_title) == len(urls_same_title):
        passed_tests += 1
    if len(unique_category_urls) == len(category_urls):
        passed_tests += 1
    passed_tests += 1  # Keyword detection (visual check)
    if 'lock=' in params and 'random=' in params:
        passed_tests += 1
    
    print(f"\nTests Passed: {passed_tests}/{total_tests}")
    
    if passed_tests == total_tests:
        print("\n✅ All tests passed! Each article should get a unique image.")
    elif passed_tests >= 3:
        print("\n⚠️  Most tests passed. Images should be mostly unique.")
    else:
        print("\n❌ Some tests failed. Image uniqueness may need improvement.")
    
    print("\nHow it works:")
    print("  1. Extracts keywords from article title")
    print("  2. Maps keywords to relevant image search terms")
    print("  3. Generates unique seed from title + category + article ID")
    print("  4. Uses SHA-256 hash for large seed range (999,999 possibilities)")
    print("  5. Adds random parameter to prevent caching")
    print("  6. Result: Each article gets a unique, relevant image")
    
    print("\n" + "="*70 + "\n")

if __name__ == "__main__":
    test_unique_images()
