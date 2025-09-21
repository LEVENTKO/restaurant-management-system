# Use slim image with Python
FROM python:3.11-slim

# Install system deps (tesseract & libs)
RUN apt-get update && apt-get install -y --no-install-recommends \
    tesseract-ocr \
    libglib2.0-0 libsm6 libxext6 libxrender1 \
    && rm -rf /var/lib/apt/lists/*

# Workdir
WORKDIR /app

# Copy files
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy app source
COPY . .

# Streamlit needs a config to listen on the Cloud Run port
ENV PORT=8080
ENV STREAMLIT_SERVER_PORT=8080
ENV STREAMLIT_SERVER_HEADLESS=true
ENV STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Optional: reduce Streamlit logs
RUN mkdir -p .streamlit
RUN printf "[server]\nheadless = true\nport = 8080\nenableCORS = false\nenableXsrfProtection = true\n" > .streamlit/config.toml

# Expose and run
EXPOSE 8080
CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]
