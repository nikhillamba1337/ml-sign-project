# 🚀 Quick Start Guide - Sign Language Detector with Streamlit

## 1️⃣ Run Locally (5 minutes)

### Windows:
```bash
# Navigate to project directory
cd C:\Users\nikhi\Desktop\ml-sign-project

# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run app.py
```

### Mac/Linux:
```bash
cd ~/Desktop/ml-sign-project
pip install -r requirements.txt
streamlit run app.py
```

✅ App will open at: http://localhost:8501

---

## 2️⃣ Deploy to Streamlit Cloud (Free & Easiest)

### Step 1: Prepare GitHub
```bash
# Initialize git repository
git init
git add .
git commit -m "Add Streamlit app"
```

### Step 2: Create GitHub Repo
- Go to https://github.com/new
- Create repo named `ml-sign-project`
- Copy the commands shown:
```bash
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ml-sign-project.git
git push -u origin main
```

### Step 3: Deploy on Streamlit Cloud
1. Go to https://streamlit.io/cloud
2. Sign in with GitHub
3. Click "New app"
4. Select:
   - Repository: `YOUR_USERNAME/ml-sign-project`
   - Branch: `main`
   - Main file path: `app.py`
5. Click "Deploy"

✅ Your app will be live at: `https://YOUR_USERNAME-ml-sign-project.streamlit.app`

---

## 3️⃣ Deploy with Docker (Optional - for servers)

### Requirements:
- Docker installed (https://www.docker.com/products/docker-desktop)

### Run:
```bash
# Build the Docker image
docker build -t sign-language-detector .

# Run the container
docker run -p 8501:8501 sign-language-detector
```

✅ Access at: http://localhost:8501

### Or use Docker Compose:
```bash
docker-compose up
```

---

## 📋 What's Included

| File | Purpose |
|------|---------|
| `app.py` | Main Streamlit application |
| `requirements.txt` | Python dependencies |
| `.streamlit/config.toml` | Streamlit configuration |
| `Dockerfile` | Docker container setup |
| `docker-compose.yml` | Docker Compose configuration |
| `.gitignore` | Git ignore rules |
| `DEPLOYMENT.md` | Detailed deployment guide |

---

## 🎯 Testing the App

1. **Allow Camera Access** - Click "Start" button
2. **Make Hand Signs** - Show letters A-Z with your hand
3. **See Predictions** - Letters appear in real-time
4. **Build Text** - Text accumulates automatically
5. **Use Buttons** - Manage with sidebar controls

---

## 🔧 Tips

- **Best on Chrome/Firefox** - Better camera support
- **Good lighting** - Essential for accurate detection
- **Stable internet** - For Streamlit Cloud deployment
- **Model file required** - Make sure `model.p` is in the project folder

---

## 📖 Full Details

See [DEPLOYMENT.md](DEPLOYMENT.md) for all deployment options and troubleshooting.

---

## ❓ Common Issues

**"Permission denied for camera"**
- Check browser camera permissions
- Try a different browser
- Refresh the page

**"Module not found"**
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

**"Model.p not found"**
- Ensure `model.p` is in the project root directory
- Check file isn't accidentally in a subfolder

**"Port 8501 already in use"**
```bash
streamlit run app.py --server.port 8502
```

---

## 📞 Support

For more help, see:
- Streamlit Docs: https://docs.streamlit.io
- MediaPipe Docs: https://developers.google.com/mediapipe
- OpenCV Docs: https://docs.opencv.org

---

**Happy deploying! 🎉**
