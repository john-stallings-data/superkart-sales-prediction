
# Use a lightweight Python 3.12 environment
FROM python:3.12-slim

# Prevent Python from creating cache files and buffer delays
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Define the default Flask backend address
ENV BACKEND_URL=http://backend:7860

# Set the application directory inside the container
WORKDIR /app

# Copy and install the frontend dependencies
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the Streamlit application
COPY app.py .

# Create a user that does not have root privileges
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

# Document the Streamlit port
EXPOSE 8501

# Confirm that the Streamlit service remains available
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8501/_stcore/health', timeout=5)" || exit 1

# Start the Streamlit application
CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0", "--server.headless=true"]
