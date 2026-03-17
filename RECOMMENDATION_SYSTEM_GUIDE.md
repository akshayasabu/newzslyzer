# Personalized News Recommendation System - User Guide

## Overview

Your news website now features an intelligent, AI-powered recommendation system that learns from user reading habits and provides personalized news recommendations. The system automatically tracks what users read and adapts the homepage to show content they're most likely to be interested in.

## How It Works

### 1. Reading History Tracking
- **Automatic Tracking**: Every time a user reads an article, the system automatically records:
  - Article ID
  - Category (Sports, Tech, Politics, etc.)
  - Timestamp
  
- **No User Action Required**: Tracking happens seamlessly in the background

### 2. Preference Calculation
- **Category Scoring**: The system counts how many articles a user reads from each category
- **Dynamic Updates**: Preferences update in real-time as users read more articles
- **Top Preferences**: The system identifies the top 3 categories a user is most interested in

### 3. Personalized Homepage
When a user logs in, they see:

#### A. AI Recommendations Section
- **Location**: Top of the homepage (after search bar)
- **Content**: 4 personalized article recommendations
- **Visual Indicators**:
  - ✨ "RECOMMENDED FOR YOU" header
  - "Personalized by AI" badge
  - Purple border around recommendation cards
  - ⭐ "For You" tag on each article
  - "Your Interests" tags showing top categories

#### B. Prioritized News Feed
- Articles from preferred categories appear first
- "Top Pick for You" badge on articles matching user interests
- Remaining articles sorted by relevance

#### C. New User Experience
- Users without reading history see a welcome message
- Encourages them to start reading to get personalized recommendations

## User Experience Flow

### First-Time User
1. **Login** → See general news feed
2. **Read Articles** → System tracks preferences
3. **Continue Reading** → Preferences strengthen
4. **Logout & Login Again** → See personalized recommendations!

### Returning User
1. **Login** → Immediately see personalized content
2. **AI Recommendations** → Top 4 articles based on reading history
3. **Prioritized Feed** → News sorted by interests
4. **Visual Indicators** → Clear labels showing personalized content

## Example Scenario

**User: John**
- Reads 5 Sports articles
- Reads 3 Tech articles  
- Reads 1 Politics article

**Result:**
- Preferences: Sports (5), Tech (3), Politics (1)
- Homepage shows:
  - "Your Interests: Sports, Tech, Politics"
  - 4 AI recommendations (mostly Sports and Tech)
  - News feed prioritizes Sports and Tech articles
  - "Top Pick for You" badges on relevant articles

## Technical Details

### Database Models

#### ReadingHistory
```python
- user_id: Links to user account
- article_id: Unique article identifier
- category: Article category
- timestamp: When article was read
```

#### UserPreference
```python
- user_id: Links to user account
- category: Category name
- score: Number of articles read in this category
```

### AI Recommendation Algorithm

The system uses a sophisticated scoring algorithm that considers:

1. **Category Preference** (Weight: 5x)
   - Articles from frequently read categories get higher scores

2. **Deep Reading Bonus** (Weight: 10x)
   - Articles from categories where user spent 30+ seconds reading

3. **Search History Match** (Weight: 30x for title, 15x for content)
   - Articles matching recent search terms

4. **Novelty Factor**
   - Already-read articles are excluded from recommendations

5. **Recency**
   - Recent articles are prioritized

### Privacy & Data

- **User Data**: All reading history is private and user-specific
- **No Sharing**: Preferences are never shared with other users
- **Opt-Out**: Users can clear their history from their profile page
- **Secure**: All data is stored securely in the database

## Testing the System

### Manual Test
1. Create a test account or use existing account
2. Read 3-5 articles from the same category (e.g., Sports)
3. Log out
4. Log back in
5. Check homepage for:
   - "RECOMMENDED FOR YOU" section
   - "Your Interests" showing Sports
   - Sports articles in recommendations

### Automated Test
Run the test script:
```bash
python test_recommendations.py
```

This will:
- Create a test user
- Simulate reading articles
- Verify preference tracking
- Test recommendation algorithm
- Display results

## Benefits

### For Users
- ✅ Save time finding relevant news
- ✅ Discover articles matching their interests
- ✅ Personalized experience that improves over time
- ✅ No manual configuration needed

### For Website
- ✅ Increased user engagement
- ✅ Higher article read rates
- ✅ Better user retention
- ✅ Data-driven content insights

## Troubleshooting

### "No recommendations showing"
- **Cause**: User hasn't read enough articles yet
- **Solution**: Read 3-5 articles from any category

### "Recommendations don't match my interests"
- **Cause**: Need more reading history
- **Solution**: Continue reading preferred categories

### "Want to reset preferences"
- **Solution**: Contact admin or clear browser data and start fresh

## Future Enhancements

Potential improvements for the system:
- Time-decay for old preferences
- Cross-category recommendations
- Trending topics integration
- Social recommendations (what similar users read)
- Email digest of personalized news
- Mobile app push notifications

## Technical Support

For issues or questions:
1. Check the test script output: `python test_recommendations.py`
2. Review Flask console logs for tracking errors
3. Verify database tables exist: `reading_history`, `user_preference`
4. Check that `track_reading_history()` is called in article routes

## Summary

The personalized recommendation system is **fully functional** and requires **no additional setup**. It works automatically as users read articles, providing an increasingly personalized experience with each visit.

Key Features:
- ✅ Automatic reading history tracking
- ✅ Real-time preference calculation
- ✅ AI-powered recommendations
- ✅ Visual indicators for personalized content
- ✅ Category-based article sorting
- ✅ New user onboarding message

The system is designed to be invisible to users while providing maximum value through intelligent content personalization.
