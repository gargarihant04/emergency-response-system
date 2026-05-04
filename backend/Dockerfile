# 1. Use an official, lightweight Python runtime
FROM python:3.11-slim

# 2. Prevent Python from writing .pyc files and keep stdout unbuffered for logging
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# 3. Set the working directory inside the container
WORKDIR /app

# 4. Install system dependencies required for database connections
RUN apt-get update \
    && apt-get install -y libpq-dev gcc \
    && rm -rf /var/lib/apt/lists/*

# 5. Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# 6. Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# 7. Copy the rest of the application code
# Using '.' instead of 'main.py' ensures if you add more files later, they get copied!
COPY . .

# 8. Expose the port FastAPI runs on
EXPOSE 8000

# 9. Command to boot the server
CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]