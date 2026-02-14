# Deploy to Render (Free Tier)

Deploy Activity Planner to Render with the backend API and frontend as separate free services.

## Prerequisites

- GitHub account
- Render account (free at [render.com](https://render.com))
- Code pushed to a GitHub repository

## Step 1: Connect Repository

1. Go to [dashboard.render.com](https://dashboard.render.com)
2. Click **New** → **Blueprint**
3. Connect your GitHub account and select your repository
4. Render will detect `render.yaml` and show both services

## Step 2: Deploy Backend First

1. Click **Apply** to create the services
2. The backend (`activity-planner-api`) will deploy first
3. Wait for it to finish (2–5 minutes)
4. Copy the backend URL: `https://activity-planner-1-jvw3.onrender.com` (or your custom name)

## Step 3: Set Environment Variables

**Important:** Use your **actual** Render URLs from the dashboard. Render assigns unique URLs (e.g. `activity-planner-5vb9.onrender.com`) when the default name is taken.

### Backend (activity-planner-api)

In the backend service → **Environment**:

| Key | Value |
|-----|-------|
| `FRONTEND_URL` | `https://activity-planner-5vb9.onrender.com` |
| `GOOGLE_REDIRECT_URI` | `https://activity-planner-1-jvw3.onrender.com/v1/auth/google/callback` |

Add any API keys you use (optional):

- `GOOGLE_PLACES_API_KEY`
- `MANUS_API_KEY`
- `GOOGLE_CLIENT_ID`, `GOOGLE_CLIENT_SECRET` (for Sign in with Google)

### Frontend (activity-planner)

In the frontend service → **Environment**:

| Key | Value |
|-----|-------|
| `API_URL` | `https://activity-planner-1-jvw3.onrender.com` |

## Step 4: Redeploy Frontend

After setting `API_URL`, trigger a manual deploy for the frontend:

1. Go to the frontend service
2. Click **Manual Deploy** → **Deploy latest commit**

## Step 5: Update Google OAuth (if using Sign in with Google)

In [Google Cloud Console](https://console.cloud.google.com/) → APIs & Services → Credentials:

1. Edit your OAuth 2.0 Client ID
2. **Authorized JavaScript origins:** add `https://activity-planner-5vb9.onrender.com`
3. **Authorized redirect URIs:** add `https://activity-planner-1-jvw3.onrender.com/v1/auth/google/callback`

## Free Tier Notes

- **Backend:** Spins down after ~15 minutes of inactivity. First request after that may take 30–60 seconds (cold start).
- **Frontend:** Always on, served from CDN.
- **Database:** SQLite file is ephemeral on free tier; data may reset on redeploy. For persistent data, add a Render Postgres database (paid).

## Custom Domain (Optional)

1. In each service → **Settings** → **Custom Domains**
2. Add your domain and follow Render’s DNS instructions

## Troubleshooting

- **CORS errors:** Ensure `FRONTEND_URL` on the backend matches your frontend URL.
- **API calls fail:** Check `API_URL` on the frontend and that the backend is running.
- **Cold starts:** Free backend sleeps when idle; first load can be slow.
