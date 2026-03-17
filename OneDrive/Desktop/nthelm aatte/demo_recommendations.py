#!/usr/bin/env python
"""
Demo script to show how the recommendation system works
This simulates a user's journey through the website
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app, db, User, ReadingHistory, UserPreference, track_reading_history, get_ai_recommendations

def print_section(title):
    """Print a formatted section header"""
    print("\n" + "="*70)
    print(f"  {title}")
    print("="*70)

def demo_user_journey():
    """Demonstrate a typical user journey with recommendations"""
    
    with app.app_context():
        print("\n" + "🎯 "*20)
        print("PERSONALIZED NEWS RECOMMENDATION SYSTEM - LIVE DEMO")
        print("🎯 "*20)
        
        # Step 1: User Registration
        print_section("STEP 1: New User Registers")
        
        demo_user = User.query.filter_by(username='demo_user_2024').first()
        if not demo_user:
            demo_user = User(
                username='demo_user_2024',
                email='demo2024@example.com',
                full_name='Demo User'
            )
            demo_user.set_password('Demo@123')
            db.session.add(demo_user)
            db.session.commit()
            print(f"✓ New user created: {demo_user.username}")
        else:
            print(f"✓ Using existing user: {demo_user.username}")
        
        print(f"  User ID: {demo_user.id}")
        print(f"  Status: No reading history yet")
        
        # Step 2: User starts reading articles
        print_section("STEP 2: User Reads Articles Over Time")
        
        reading_sessions = [
            ("Day 1 - Morning", [
                ('sports_article_1', 'Sports', 'Cricket Match Highlights'),
                ('sports_article_2', 'Sports', 'Football Championship Update'),
            ]),
            ("Day 1 - Evening", [
                ('sports_article_3', 'Sports', 'Tennis Tournament Results'),
                ('tech_article_1', 'Tech', 'New Smartphone Launch'),
            ]),
            ("Day 2 - Morning", [
                ('sports_article_4', 'Sports', 'Olympics Preview'),
                ('sports_article_5', 'Sports', 'Basketball Finals'),
                ('tech_article_2', 'Tech', 'AI Breakthrough Announced'),
            ]),
            ("Day 3 - Evening", [
                ('tech_article_3', 'Tech', 'Latest Gadget Reviews'),
                ('politics_article_1', 'Politics', 'Election Updates'),
            ])
        ]
        
        for session_name, articles in reading_sessions:
            print(f"\n📅 {session_name}")
            for article_id, category, title in articles:
                track_reading_history(demo_user.id, article_id, category)
                print(f"   📰 Read: {title} ({category})")
        
        # Step 3: Show user preferences
        print_section("STEP 3: System Calculates User Preferences")
        
        preferences = UserPreference.query.filter_by(user_id=demo_user.id).order_by(UserPreference.score.desc()).all()
        
        if preferences:
            print("\n📊 User's Reading Preferences:")
            total_reads = sum(p.score for p in preferences)
            for i, pref in enumerate(preferences, 1):
                percentage = (pref.score / total_reads) * 100
                bar = "█" * int(percentage / 5)
                print(f"   {i}. {pref.category:15} {bar} {pref.score} articles ({percentage:.1f}%)")
        
        # Step 4: Generate recommendations
        print_section("STEP 4: AI Generates Personalized Recommendations")
        
        sample_articles = [
            {'id': 'new_1', 'title': 'Breaking: Major Sports Event', 'category': 'Sports', 'excerpt': 'Latest sports news'},
            {'id': 'new_2', 'title': 'Tech Innovation Unveiled', 'category': 'Tech', 'excerpt': 'New technology breakthrough'},
            {'id': 'new_3', 'title': 'Political Debate Highlights', 'category': 'Politics', 'excerpt': 'Latest political news'},
            {'id': 'new_4', 'title': 'Entertainment Buzz', 'category': 'Entertainment', 'excerpt': 'Celebrity updates'},
            {'id': 'new_5', 'title': 'Sports Championship Finals', 'category': 'Sports', 'excerpt': 'Championship results'},
            {'id': 'new_6', 'title': 'Tech Gadget Launch', 'category': 'Tech', 'excerpt': 'New gadget releases'},
            {'id': 'new_7', 'title': 'Health & Wellness Tips', 'category': 'Health', 'excerpt': 'Health advice'},
            {'id': 'new_8', 'title': 'Business Market Update', 'category': 'Business', 'excerpt': 'Market analysis'},
        ]
        
        recommendations = get_ai_recommendations(demo_user.id, sample_articles, limit=4)
        
        if recommendations:
            print("\n✨ Top 4 Personalized Recommendations:")
            for i, rec in enumerate(recommendations, 1):
                print(f"   {i}. 📰 {rec['title']}")
                print(f"      Category: {rec['category']} | Reason: Matches your interests")
        
        # Step 5: Show what user sees on homepage
        print_section("STEP 5: User Logs In - Homepage Experience")
        
        print("\n🏠 Homepage Layout:")
        print("\n┌─────────────────────────────────────────────────────────────┐")
        print("│  ✨ RECOMMENDED FOR YOU  [Personalized by AI]              │")
        print("│  Your Interests: Sports, Tech, Politics                     │")
        print("├─────────────────────────────────────────────────────────────┤")
        
        for i, rec in enumerate(recommendations[:4], 1):
            print(f"│  [{i}] {rec['title'][:50]:50} │")
            print(f"│      ⭐ For You | {rec['category']:15} | 📊 Based on history │")
            print("├─────────────────────────────────────────────────────────────┤")
        
        print("│                                                             │")
        print("│  TRENDING NOW                                               │")
        print("│  (Articles sorted by your preferences)                      │")
        print("└─────────────────────────────────────────────────────────────┘")
        
        # Summary
        print_section("SUMMARY: How The System Works")
        
        print("""
The recommendation system provides a personalized experience through:

1. 📖 AUTOMATIC TRACKING
   - Tracks every article a user reads
   - Records category and timestamp
   - No user action required

2. 🧠 SMART LEARNING
   - Calculates preferences based on reading frequency
   - Identifies top 3 favorite categories
   - Updates in real-time

3. ✨ PERSONALIZED CONTENT
   - Shows AI recommendations on homepage
   - Displays "Your Interests" tags
   - Prioritizes articles from preferred categories
   - Adds "Top Pick for You" badges

4. 🎯 CONTINUOUS IMPROVEMENT
   - Gets better with more reading
   - Adapts to changing interests
   - Provides increasingly relevant content

RESULT: Users see news they care about, increasing engagement and satisfaction!
        """)
        
        print("\n" + "🎯 "*20)
        print("Demo Complete! The system is ready to use.")
        print("🎯 "*20 + "\n")

if __name__ == "__main__":
    demo_user_journey()
