# Railway Environment Variables Setup

## Frontend Service Configuration

Frontend needs to know where the backend API is located. Add this environment variable in Railway:

### 1. Go to Railway Dashboard
- Open your project: RelatriX_v1
- Click on `frontend` service

### 2. Add Environment Variable
- Go to "Variables" tab
- Click "New Variable"
- Add:
  ```
  VITE_API_URL=https://relatrix-backend.up.railway.app
  ```

### 3. Redeploy Frontend
- Click "Deploy" → "Redeploy"
- Wait for deployment to complete

## Verify Configuration

After deployment, check:
1. Visit: https://relatrix-frontend.up.railway.app
2. Open browser Developer Tools (F12)
3. Go to Network tab
4. Try to login or access admin panel
5. API calls should go to: `https://relatrix-backend.up.railway.app/api/...`

## Troubleshooting

If still getting Network Error:
1. Check backend logs for CORS errors
2. Verify backend is running: https://relatrix-backend.up.railway.app/health
3. Check if frontend shows correct API URL in Admin panel header

## Clean Up Duplicate Agents

To remove duplicate agents:
1. Login to admin panel
2. Open Developer Console (F12)
3. Run:
```javascript
fetch('https://relatrix-backend.up.railway.app/api/agents/cleanup-duplicates', {
  method: 'DELETE',
  headers: {
    'Authorization': 'Bearer ' + localStorage.getItem('relatrix_token')
  }
}).then(r => r.json()).then(console.log)
```

This will remove all duplicate agents, keeping only one of each type.