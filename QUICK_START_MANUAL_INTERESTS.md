# Manual Interest Selection - Quick Start

## ✅ Feature Status: READY TO USE

## For Users

### How to Set Your Interests

1. **Log in** to the website
2. **Go to Profile** (click "My Account" → "MY PROFILE")
3. **Scroll down** to "📰 News Interests" section
4. **Click categories** you're interested in (they'll turn purple with a checkmark)
5. **Click "Save Interests"** button
6. **Log out and log back in** to see personalized recommendations!

### What You'll See

- **Profile Page**: Interactive category cards with icons
- **Homepage**: "RECOMMENDED FOR YOU" section with your selected categories
- **News Feed**: Articles sorted by your interests

## For Developers

### Quick Test

```bash
# Run automated test
python test_manual_interests.py
```

### Database Migration

```bash
# Already done! But if needed:
python migrate_manual_interests.py
```

### Files Modified

- `app.py` - Added manual_interests field and routes
- `templates/profile.html` - Added UI for interest selection

## How It Works

```
User selects categories → Stored in database → Boost preference scores
                                             ↓
                                    Apply 15x weight in algorithm
                                             ↓
                                    Show personalized content
```

## Key Features

✅ 18 category options with icons  
✅ Interactive checkbox cards  
✅ Immediate effect on recommendations  
✅ Combined with automatic tracking  
✅ Responsive design  
✅ All existing features preserved  

## Priority System

1. **Manual Interests** - 75 points (HIGHEST)
2. **Reading History** - 5-10 points per read
3. **Deep Reading** - 2x bonus (30+ seconds)
4. **Search Keywords** - 15-30 points

## Example

**User selects:** Sports, Tech  
**User reads:** 5 Sports articles  
**Result:** Homepage shows mostly Sports and Tech news!

## Testing

### Automated
```bash
python test_manual_interests.py
```
Expected: All tests pass ✓

### Manual
1. Select interests in profile
2. Save
3. Log out/in
4. Check homepage recommendations

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Column not found | Run `python migrate_manual_interests.py` |
| Interests not saving | Check browser console for errors |
| No recommendations | Log out and log back in |

## Documentation

- `MANUAL_INTERESTS_GUIDE.md` - Complete guide
- `MANUAL_INTERESTS_COMPLETE.txt` - Implementation summary
- `test_manual_interests.py` - Test script

---

**Status**: ✅ Production Ready  
**Version**: 1.0  
**Date**: March 9, 2026
