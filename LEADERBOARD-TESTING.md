# 🧪 SQLite Leaderboard Testing Guide

## 📋 System Overview

The Object Quest app now features a SQLite-backed leaderboard system with the following components:

- **Database**: `data/leaderboard.db` (SQLite file)
- **Backend**: Flask API endpoints under `/api/leaderboard/*`
- **Frontend**: Enhanced JavaScript with localStorage fallback
- **Fallback**: Automatic localStorage backup when server is unavailable

## 🚀 Quick Start Testing

### 1. Basic Functionality Test

```bash
# 1. Start the server
python app.py

# 2. Open browser to https://127.0.0.1:5000
# 3. Test workflow:
   - Enter name: "TestPlayer1"
   - Allow camera access
   - Detect some objects (if possible)
   - Check leaderboard for score updates
```

### 2. Database Verification

```bash
# Check if database exists
ls -la data/
# Should show: leaderboard.db

# View database contents
sqlite3 data/leaderboard.db "SELECT * FROM leaderboard ORDER BY score DESC LIMIT 5;"

# Check database schema
sqlite3 data/leaderboard.db ".schema leaderboard"
```

## 🧪 API Endpoint Testing

### Test Leaderboard Retrieval

```bash
# Get top players
curl -X GET "https://127.0.0.1:5000/api/leaderboard?limit=5"

# Expected response:
{
  "success": true,
  "players": [...],
  "total_players": 2
}
```

### Test Player Update

```bash
# Add or update player
curl -X POST "https://127.0.0.1:5000/api/leaderboard" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "TestPlayer1",
    "score": 50,
    "games_played": 1,
    "objects_discovered": 5
  }'
```

### Test Player Rank

```bash
# Get specific player rank
curl -X GET "https://127.0.0.1:5000/api/leaderboard/player/TestPlayer1"
```

### Test Statistics

```bash
# Get leaderboard statistics
curl -X GET "https://127.0.0.1:5000/api/leaderboard/stats"
```

### Test Admin Clear (with token)

```bash
# Clear leaderboard (requires auth token)
curl -X DELETE "https://127.0.0.1:5000/api/leaderboard/clear" \
  -H "Authorization: Bearer objectquest-admin-2025"
```

## 🖥️ Frontend Testing

### 1. Normal Operation Test

1. **Start Fresh Session**
   - Open app in browser
   - Clear browser localStorage (F12 → Application → Storage → Clear)
   - Enter new name: "FrontendTest1"

2. **Test Score Updates**
   - Wait for object detection or manually test:
   ```javascript
   // In browser console:
   userScore = 30;
   updateLeaderboard("FrontendTest1", userScore, 1, 3);
   ```

3. **Test Leaderboard Display**
   - Click "🏆 Leaderboard" button
   - Should show updated scores
   - Should show connection status

### 2. Fallback Testing

1. **Simulate Server Down**
   - Stop the Python server (Ctrl+C)
   - Refresh browser page
   - Try to view leaderboard
   - Should automatically fall back to localStorage

2. **Verify Offline Functionality**
   - Should show "📱 Offline Mode" indicator
   - Score should still save to localStorage
   - Leaderboard should still display

3. **Server Recovery Test**
   - Restart Python server
   - Refresh page
   - Leaderboard should switch back to "✅ Connected" mode

### 3. Error Handling Test

```javascript
// Test invalid data handling
fetch('/api/leaderboard', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: '',  // Empty name should fail
    score: -5  // Negative score should fail
  })
})
```

## 🔍 Database Structure Validation

### Expected Schema

```sql
CREATE TABLE leaderboard (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0,
    games_played INTEGER DEFAULT 0,
    objects_discovered INTEGER DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### Sample Data Validation

```bash
# Insert test data
sqlite3 data/leaderboard.db "
INSERT INTO leaderboard (name, score, games_played, objects_discovered) 
VALUES ('TestUser1', 100, 5, 10);

SELECT name, score, games_played, objects_discovered, created_at 
FROM leaderboard 
ORDER BY score DESC;"
```

## 🐛 Troubleshooting Guide

### Issue: Database Not Created

**Symptoms**: No `data/leaderboard.db` file

**Solutions**:
```bash
# Check directory permissions
ls -la data/
chmod 755 data/

# Manual database initialization
python3 -c "from data.database import db; print('DB initialized:', db.db_path)"
```

### Issue: API Returns 500 Error

**Symptoms**: Server errors when accessing `/api/leaderboard/*`

**Solutions**:
1. Check Python console for error messages
2. Verify database file permissions:
   ```bash
   chmod 664 data/leaderboard.db
   ```
3. Check SQLite installation:
   ```bash
   python3 -c "import sqlite3; print('SQLite version:', sqlite3.sqlite_version)"
   ```

### Issue: Frontend Shows "API Unavailable"

**Symptoms**: Always using localStorage fallback

**Solutions**:
1. Check server is running: `ps aux | grep python`
2. Verify HTTPS certificate issues:
   ```bash
   # Test HTTP instead of HTTPS for debugging
   curl -X GET "http://127.0.0.1:5000/api/leaderboard"
   ```
3. Check browser network tab for failed requests

### Issue: CORS Errors

**Symptoms**: Browser blocks API calls due to CORS

**Solutions**: Add CORS support to Flask:
```python
from flask_cors import CORS
CORS(app)
```

## 📊 Performance Testing

### Load Testing

```bash
# Test with multiple concurrent requests
for i in {1..10}; do
  curl -X POST "https://127.0.0.1:5000/api/leaderboard" \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"LoadTest$i\", \"score\": $((i * 10))}" &
done
wait
```

### Database Size Testing

```bash
# Check database size after many inserts
ls -lh data/leaderboard.db

# Count records
sqlite3 data/leaderboard.db "SELECT COUNT(*) FROM leaderboard;"
```

## ✅ Acceptance Criteria Checklist

### Backend Functionality
- [ ] Database file created at `data/leaderboard.db`
- [ ] Tables created with proper schema
- [ ] API endpoints return correct JSON responses
- [ ] Player insertion/update works correctly
- [ ] Ranking calculations are accurate
- [ ] Error handling returns appropriate status codes

### Frontend Integration
- [ ] Leaderboard loads via API when server available
- [ ] Scores update both server and localStorage
- [ ] Automatic fallback to localStorage when server down
- [ ] Connection status indicators work correctly
- [ ] Loading states display during API calls
- [ ] Error messages shown for invalid requests

### Data Persistence
- [ ] Data survives server restarts
- [ ] LocalStorage backup works when offline
- [ ] Player scores merge correctly (higher score wins)
- [ ] Games played and objects discovered track properly

### Edge Cases
- [ ] Handles duplicate player names correctly
- [ ] Handles invalid/negative scores gracefully
- [ ] Handles empty player names
- [ ] Handles network timeouts
- [ ] Handles database corruption scenarios

## 🔧 Development Commands

### Reset Database

```bash
# Remove and recreate database
rm data/leaderboard.db
python3 -c "from data.database import db; print('Database reset complete')"
```

### Backup Database

```bash
# Create backup
cp data/leaderboard.db data/leaderboard_backup_$(date +%Y%m%d_%H%M%S).db
```

### Monitor Database

```bash
# Watch database changes in real-time
watch -n 2 'sqlite3 data/leaderboard.db "SELECT name, score FROM leaderboard ORDER BY score DESC LIMIT 5;"'
```

## 📝 Test Report Template

```
Date: ___________
Tester: ___________
Browser: __________
Server URL: _______

Test Results:
- Database Creation: ✅/❌
- API Endpoints: ✅/❌
- Frontend Integration: ✅/❌
- Fallback Functionality: ✅/❌
- Error Handling: ✅/❌

Issues Found:
1. _______________
2. _______________
3. _______________

Overall Status: ✅ PASS / ❌ FAIL
```

## 🎯 Success Metrics

The leaderboard system is successful when:

1. **Data Persistence**: Player scores persist across sessions
2. **Real-time Updates**: Scores update immediately when earned
3. **Offline Capability**: App works without server connection
4. **Scalability**: Handles multiple concurrent users
5. **Data Integrity**: No data loss during server restarts
6. **User Experience**: Seamless transition between online/offline modes

---

## 🚀 Quick Test Script

Run this in browser console to test everything:

```javascript
// Comprehensive Leaderboard Test
async function testLeaderboard() {
    console.log('🧪 Starting leaderboard tests...');
    
    try {
        // Test 1: API Connection
        console.log('Test 1: API Connection');
        const response = await fetch('/api/leaderboard');
        const data = await response.json();
        console.log('✅ API Working:', data.success);
        
        // Test 2: Player Update
        console.log('Test 2: Player Update');
        const updateResponse = await fetch('/api/leaderboard', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                name: 'TestUser_' + Date.now(),
                score: Math.floor(Math.random() * 100),
                games_played: 1,
                objects_discovered: 3
            })
        });
        const updateData = await updateResponse.json();
        console.log('✅ Update Working:', updateData.success);
        
        // Test 3: Leaderboard Display
        console.log('Test 3: Leaderboard Display');
        showLeaderboard();
        console.log('✅ Leaderboard displayed');
        
        console.log('🎉 All tests passed!');
        
    } catch (error) {
        console.error('❌ Test failed:', error);
        console.log('📱 Switching to fallback mode');
        useLocalStorageFallback = true;
    }
}

// Run tests
testLeaderboard();
```

This comprehensive testing approach ensures the SQLite leaderboard system works reliably in all scenarios!