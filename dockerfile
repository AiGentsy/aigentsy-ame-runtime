# 1. Use slim Python image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Install OS dependencies (for pip, poetry, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    && rm -rf /var/lib/apt/lists/*

# 4. Upgrade pip, install Python deps
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 5. Copy app files
COPY . .

# 6. Expose port
EXPOSE 8000

# 7. Start server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
