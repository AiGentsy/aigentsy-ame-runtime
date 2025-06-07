FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy only the requirements first for caching
COPY requirements.txt .

# Install system packages and Python dependencies
RUN apt-get update && apt-get install -y gcc libffi-dev libssl-dev && apt-get clean && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy the full app code
COPY . .

# Expose the default FastAPI port
EXPOSE 8000

# Start the FastAPI app using uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]

