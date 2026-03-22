# 🚀 Deployment Guide - Sign Language Detector

## ⚠️ IMPORTANT: Streamlit Cloud Limitation

**Streamlit Cloud doesn't work for this app** because:
- ❌ No camera/webcam access (headless server)
- ❌ No OpenGL libraries
- ❌ No local file system

**👉 See [STREAMLIT_DEPLOYMENT.md](STREAMLIT_DEPLOYMENT.md) for solutions!**

---

## Option 1: Railway.app (Recommended ✅)

### Steps:
1. **Install Git** (if not already installed)
   - Download from https://git-scm.com/

2. **Create a GitHub Repository**
   - Go to https://github.com/new
   - Create a new repo

3. **Push Your Code to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git branch -M main
   git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git
   git push -u origin main
   ```

4. **Deploy on Streamlit Cloud**
   - Go to https://streamlit.io/cloud
   - Click "New app"
   - Select your repo, branch, and `app.py` as the main file
   - Click "Deploy"

### ✅ Advantages:
- Always free
- Auto-deploys on every GitHub push
- No server management needed
- Perfect for live demos

---

## Option 2: Local Run (For Testing)

### Steps:
1. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run the app**
   ```bash
   streamlit run app.py
   ```

3. **Access the app**
   - Open http://localhost:8501 in your browser

### ✅ Advantages:
- Test locally before deploying
- Full control over camera access
- No internet required

---

## Option 3: Docker Deployment (Production ⚙️)

### Create a Dockerfile
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install system dependencies for OpenCV
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8501

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

### Build & Run:
```bash
# Build image
docker build -t sign-language-detector .

# Run container
docker run -p 8501:8501 sign-language-detector
```

---

## Option 4: Cloud Platforms

### Heroku (Deprecated but alternative: Railway/Render)

**Railway.app (Recommended)**
1. Go to https://railway.app
2. Click "New Project" → "Deploy from GitHub"
3. Select your repo
4. Add any environment variables if needed
5. Deploy!

**Render.com**
1. Go to https://render.com
2. Create new "Web Service"
3. Connect GitHub repo
4. Build command: `pip install -r requirements.txt`
5. Start command: `streamlit run app.py --server.port=$PORT --server.address=0.0.0.0`

**AWS/Google Cloud/Azure**
- Use EC2 (AWS), App Engine (Google), or App Service (Azure)
- Follow their Python deployment guides
- Run the Streamlit app on a VM

---

## Option 5: Running on Your Computer (System Service)

### Windows - Create a batch file:
```batch
@echo off
cd C:\Users\nikhi\Desktop\ml-sign-project
streamlit run app.py
```

Save as `start_app.bat` and run it.

### Mac/Linux - Create a shell script:
```bash
#!/bin/bash
cd ~/Desktop/ml-sign-project
streamlit run app.py
```

Save as `start_app.sh` and run with `bash start_app.sh`

---

## 🔧 Troubleshooting

### Camera not working?
- Check browser permissions (allow camera access)
- Try a different browser (Chrome works best)
- On Streamlit Cloud, camera works through browser API

### Model file not found?
- Ensure `model.p` is in the same directory as `app.py`
- Check file path is correct

### Dependencies error?
```bash
pip install --upgrade pip
pip install -r requirements.txt --force-reinstall
```

### Port already in use?
```bash
streamlit run app.py --server.port 8502
```

---

## 📊 Performance Tips

1. **Cache the model** - Already done with `@st.cache_resource`
2. **Lazy load MediaPipe** - Already optimized
3. **Use hardware acceleration** - For better performance
4. **Optimize image resolution** - Edit video constraints in app.py

---

## 🔒 Security Checklist

- [ ] Remove sensitive data from code
- [ ] Use environment variables for secrets
- [ ] Enable HTTPS (auto on Streamlit Cloud)
- [ ] Don't commit `model.p` if it contains training data
- [ ] Add `.gitignore` with sensitive files

---

## 📞 Next Steps

1. **Choose your deployment option** (Streamlit Cloud recommended)
2. **Set up GitHub repository**
3. **Update code if needed**
4. **Deploy and test**
5. **Share your app URL!**

---

Happy deploying! 🎉
