# Troubleshooting Guide

## Backend Not Showing / Recommendations Not Loading

### Step 1: Check if Backend is Running

Open a terminal and run:
```bash
curl http://localhost:5001/health
```

You should see:
```json
{"status": "ok", "service": "activity-planner-api"}
```

If you get a connection error, the backend is not running.

### Step 2: Start the Backend

```bash
cd activity-planner/backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
python app.py
```

You should see:
```
==================================================
Activity Planner Backend API
==================================================
Server starting on http://localhost:5001
API endpoints available at http://localhost:5001/v1
Health check: http://localhost:5001/health
==================================================
 * Running on http://0.0.0.0:5001
```

### Step 3: Test the API Endpoints

In another terminal, test the digest endpoint:
```bash
curl http://localhost:5001/v1/digest
```

You should get a JSON response with recommendations.

### Step 4: Check Browser Console

1. Open the frontend in your browser (http://localhost:8000)
2. Open Developer Tools (F12 or Cmd+Option+I)
3. Go to the Console tab
4. Look for any error messages

Common errors:
- `Failed to fetch` - Backend is not running or CORS issue
- `NetworkError` - Backend is not accessible
- `404 Not Found` - Wrong API endpoint URL

### Step 5: Check CORS

If you see CORS errors in the console, make sure:
- Backend is running on port 5001
- Frontend is accessing `http://localhost:5001` (not a different port)
- The backend has `CORS(app, supports_credentials=True)` configured (it does)

### Step 6: Verify Frontend is Running

```bash
cd activity-planner/frontend
python3 -m http.server 8000
```

Then open http://localhost:8000 in your browser.

## Quick Fix: Use the Startup Script

The easiest way to start both servers:

```bash
cd activity-planner
./run.sh
```

This will start both backend and frontend automatically.

## Manual Testing

### Test Backend Directly

1. Start backend: `cd backend && source venv/bin/activate && python app.py`
2. In another terminal, test endpoints:
   ```bash
   # Health check
   curl http://localhost:5001/health
   
   # Get digest (should work even without preferences)
   curl http://localhost:5001/v1/digest
   
   # Get preferences
   curl http://localhost:5001/v1/preferences
   ```

### Test Frontend

1. Make sure backend is running
2. Start frontend: `cd frontend && python3 -m http.server 8000`
3. Open http://localhost:8000
4. Click "Skip & Use Defaults" to bypass onboarding
5. Recommendations should appear

## Common Issues

### Issue: "Backend Connection Issue" banner appears

**Solution:** The backend is not running. Start it with:
```bash
cd activity-planner/backend
source venv/bin/activate
python app.py
```

### Issue: No recommendations showing

**Possible causes:**
1. Backend not running - Start the backend server
2. All places filtered out - Try adjusting preferences (increase radius, add more categories)
3. JavaScript errors - Check browser console

**Solution:** 
- Click "Skip & Use Defaults" to use default preferences
- Check browser console for errors
- Verify backend is running and accessible

### Issue: Port already in use

If you see "Address already in use":
```bash
# Find process using port 5001
lsof -i :5001

# Kill it (replace PID with actual process ID)
kill -9 <PID>
```

Or use a different port by editing `app.py`:
```python
app.run(debug=True, port=5001, host='0.0.0.0')
```

And update `frontend/app.js`:
```javascript
const API_BASE = 'http://localhost:5001/v1';
```

## Still Having Issues?

1. Check that Python 3 is installed: `python3 --version`
2. Verify dependencies are installed: `cd backend && source venv/bin/activate && pip list`
3. Check for firewall/antivirus blocking localhost connections
4. Try accessing backend directly: http://localhost:5001/health in your browser
