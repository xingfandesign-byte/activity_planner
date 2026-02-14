# Debugging Guide: No Recommendations After Onboarding

## Quick Checks

### 1. Verify Backend is Running
```bash
curl http://localhost:5001/health
```
Should return: `{"status": "ok", "service": "activity-planner-api"}`

### 2. Check Browser Console
1. Open Developer Tools (F12 or Cmd+Option+I)
2. Go to Console tab
3. Look for error messages or debug logs
4. You should see logs like:
   - "Saving preferences: ..."
   - "Preferences saved: ..."
   - "Loading digest from: ..."
   - "Digest loaded: ..."
   - "Rendering X items"

### 3. Check Backend Terminal
When you submit the onboarding form, you should see debug logs:
```
[DEBUG] Updating preferences for user demo_user: {...}
[DEBUG] Preferences saved. Categories: ['parks', 'museums', 'attractions']
[DEBUG] User ID: demo_user
[DEBUG] Preferences: {...}
[DEBUG] Categories: ['parks', 'museums', 'attractions']
[DEBUG] Filtering places - categories: [...], show_all: False
[DEBUG] Total places to filter: 10
[DEBUG] Included Golden Gate Park (parks)
...
[DEBUG] Final result count: 8
[DEBUG] Returning 8 items
```

## Common Issues

### Issue: No Categories Selected
**Symptom:** Form allows submission but no recommendations show

**Solution:** The form now validates that at least one category is selected. Make sure at least one checkbox is checked.

### Issue: Selected Categories Don't Match Available Places
**Symptom:** Only "Food" or "Events" selected, but no recommendations

**Available categories in mock data:**
- parks
- museums  
- attractions

**Solution:** Select at least one of: Parks, Museums, or Attractions

### Issue: All Places Filtered Out
**Possible causes:**
1. **Radius too small:** If you set radius to 1 mile, most places will be filtered out
2. **Kid-friendly filter:** If enabled, places like "Alcatraz Island" and "SFMOMA" are filtered out
3. **All places marked as visited:** Check visited history

**Solution:**
- Increase radius (default: 10 miles)
- Uncheck "Kid-friendly" if you want more options
- Use "Skip & Use Defaults" to see all recommendations

### Issue: Backend Not Receiving Preferences
**Symptom:** Backend logs show empty preferences

**Check:**
1. Backend terminal should show: `[DEBUG] Updating preferences for user...`
2. If not, check browser console for fetch errors
3. Verify backend is running on port 5001

### Issue: CORS Errors
**Symptom:** Browser console shows CORS errors

**Solution:**
- Make sure backend is running
- Check that frontend is accessing `http://localhost:5001`
- Backend has CORS enabled, so this shouldn't happen

## Step-by-Step Debugging

1. **Start Backend:**
   ```bash
   cd activity-planner/backend
   source venv/bin/activate
   python app.py
   ```

2. **Open Frontend:**
   - Open http://localhost:8000
   - Open Developer Tools (Console tab)

3. **Submit Onboarding Form:**
   - Fill out the form
   - Make sure at least one of: Parks, Museums, or Attractions is selected
   - Click "Get Started"
   - Watch both browser console and backend terminal

4. **Check Results:**
   - Browser console should show: "Digest loaded: {week: ..., items: [...]}"
   - Backend terminal should show: "[DEBUG] Returning X items"
   - If items.length > 0, recommendations should appear

## Testing with Defaults

If you're having issues, try:
1. Click "Skip & Use Defaults" button
2. This bypasses onboarding and uses default preferences
3. Should show 8 recommendations immediately

## Manual API Test

Test the API directly:
```bash
# Get preferences
curl http://localhost:5001/v1/preferences

# Get digest
curl http://localhost:5001/v1/digest | python3 -m json.tool
```

The digest should return a JSON object with an "items" array containing recommendations.
