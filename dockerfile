FROM python:3.10-slim

WORKDIR /app
COPY . .

# Blow away pip cache and force constraints lock
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt -c constraints.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
