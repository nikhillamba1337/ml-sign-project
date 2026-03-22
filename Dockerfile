# Dockerfile for Flask Sign Language Detector (Render-ready)

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies for OpenCV and MediaPipe
# Need OpenGL libraries even with opencv-python-headless
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libopengl0 \
    libglx0 \
    libglvnd0 \
    libgl1-mesa-dri \
    libgl1 \
    && rm -rf /var/lib/apt/lists/* \
    && ldconfig

# Copy requirements and install Python dependencies
COPY requirements_render.txt .
RUN pip install --no-cache-dir -r requirements_render.txt

# Copy the application files
COPY app_flask.py .
COPY index.html .
COPY model.p .

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/health')" || exit 1

# Run Flask app with gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "2", "--timeout", "120", "--access-logfile", "-", "--error-logfile", "-", "app_flask:app"]
