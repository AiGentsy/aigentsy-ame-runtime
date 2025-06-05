FROM python:3.10-slim

WORKDIR /app

COPY . .

# ✅ Force exact versions, bypassing pip resolver issues
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      langchain==0.1.13 \
      langchain-openai==0.0.8 \
      openai==1.25.0 \
      langgraph==0.0.40 \
      fastapi==0.110.0 \
      uvicorn==0.29.0

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
