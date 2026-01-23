# 1. Use slim Python image
FROM python:3.11-slim

# 2. Set working directory
WORKDIR /app

# 3. Install OS dependencies (including Playwright browser deps)
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    # Playwright Chromium dependencies
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2 \
    libpango-1.0-0 \
    libcairo2 \
    && rm -rf /var/lib/apt/lists/*

# 4. Upgrade pip and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip setuptools wheel && \
    pip install --no-cache-dir -r requirements.txt

# 5. Install Playwright browsers (Chromium only for smaller image)
RUN python -m playwright install chromium --with-deps

# 6. Copy app files
COPY . .

# 7. Expose port
EXPOSE 8000

# 8. Dynamic entrypoint for agent variant
CMD sh -c "uvicorn ${AGENT_ENTRYPOINT:-main}:app --host 0.0.0.0 --port 8000"
