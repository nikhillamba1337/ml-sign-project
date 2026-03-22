# 🚀 Deployment Guide - Flask + Render

This guide explains how to deploy the Sign Language Detector on Render with browser-based camera access.

## Architecture Overview

- **Frontend**: HTML/JavaScript runs in user's browser
- **Camera**: Accessed directly from browser (no server-side camera needed)
- **Backend**: Flask API on Render processes frames and runs ML model
- **Processing**: Browser sends video frames → Render processes → Returns predictions

## Why This Works on Render

✅ **Browser camera capture** - Users give permission directly to browser
✅ **No system cameras needed** - Server doesn't need a camera
✅ **Privacy-first** - All video stays on user's machine
✅ **Works globally** - Users from anywhere can use it
✅ **Simple deployment** - Standard Flask app on Render

## Local Setup & Testing

### 1. Install Dependencies
```bash
pip install -r requirements_render.txt
```

### 2. Run Locally
```bash
python app_flask.py
```

Then visit: **http://localhost:5000**

### 3. Test Features
- Click "Start Detection" button
- Allow browser camera access
- Show signs - see letters detected in real-time
- Use keyboard shortcuts (W, S, B, V, C, Q)

## Deploy on Render

### Option A: Deploy from GitHub (Recommended)

1. **Push code to GitHub**
   ```bash
   git add -A
   git commit -m "Add Flask app for Render deployment"
   git push
   ```

2. **Create New Web Service on Render**
   - Go to [render.com](https://render.com)
   - Click "New +" → "Web Service"
   - Connect your GitHub repository
   - Choose branch: `main` (or your branch)

3. **Configure Settings**
   ```
   Name: sign-language-detector
   Runtime: Python 3
   Build Command: pip install -r requirements_render.txt
   Start Command: gunicorn app_flask:app
   ```

4. **Set Environment Variables (if needed)**
   - Go to "Environment" tab
   - Add `PYTHONUNBUFFERED`: `true`

5. **Deploy**
   - Click "Create Web Service"
   - Wait for deployment (2-5 minutes)
   - Your app will be live at: `https://your-app-name.onrender.com`

### Option B: Deploy via Render CLI

```bash
# Install Render CLI
npm install -g render-cli

# Login
render login

# Deploy
render deploy
```

## Files Explained

### `app_flask.py`
- Main Flask backend server
- Loads the ML model
- Receives video frames from browser
- Returns detected letters

### `templates/index.html`
- Web interface
- Handles camera capture
- Sends frames to backend
- Displays results in real-time

### `requirements_render.txt`
- Python dependencies for Render
- Uses `gunicorn` for production server
- `opencv-python-headless` (no GUI needed)

### `Procfile`
- Tells Render how to start the app
- Runs: `gunicorn app_flask:app`

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| **W** | Capture current letter |
| **S** | Delete last letter |
| **B** | Delete last letter (alternative) |
| **V** | Add space |
| **C** | Clear all text |
| **Q** | Stop detection |

## Troubleshooting

### App won't start
- Check Render logs: Dashboard → Web Service → Logs
- Ensure `Procfile` exists and is correct
- Verify `requirements_render.txt` is spelled correctly

### Camera doesn't work
- Browser needs HTTPS or localhost
- Allow camera permission when prompted
- Check browser console (F12) for errors

### Model not found
- Ensure `model.p` is in project root
- Push it to GitHub or upload to Render storage

### Slow performance
- Model inference takes ~100-200ms per frame
- Expected FPS: 5-10 on Render (normal for cloud processing)

## Size Limitations

- Max request size: 16MB (for video frames)
- Render free tier: 750 hours/month
- Recommended for hobby/educational use

## Production Optimization Tips

1. **Use Render Cron Jobs** for periodic restarts
2. **Add monitoring** with Sentry for errors
3. **Use Redis cache** for session management
4. **Enable auto-scaling** for concurrent users

## Local vs Cloud Comparison

| Feature | Local | Render Cloud |
|---------|-------|-------------|
| Speed | Fast (30 FPS) | Slower (5-10 FPS) |
| Camera | Direct access | Browser capture |
| Cost | Free | Free tier available |
| Always on | Depends | 24/7 available |
| Setup | 1 command | GitHub + Render |

## Support

For issues:
1. Check Render logs
2. Test locally first: `python app_flask.py`
3. Verify all files are pushed to GitHub
4. Check browser console (F12) for JS errors

---

**Ready to deploy?** Push to GitHub and click the Render deploy button! 🚀
