
# Use a lightweight Python 3.12 environment
FROM python:3.12-slim

# Prevent Python from creating cache files and buffer delays
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set the application directory inside the container
WORKDIR /app

# Copy and install dependencies before copying the remaining files
COPY requirements.txt .

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy the Flask application and serialized model
COPY app.py .
COPY superkart_model.joblib .

# Create a user that does not have root privileges
RUN useradd --create-home appuser \
    && chown -R appuser:appuser /app

USER appuser

# Document the port used by the Flask API
EXPOSE 7860

# Confirm that the API remains available
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:7860/health', timeout=5)" || exit 1

# Start the Flask application using Gunicorn
CMD ["gunicorn", "--workers", "2", "--threads", "2", "--timeout", "120", "--bind", "0.0.0.0:7860", "app:superkart_api"]
