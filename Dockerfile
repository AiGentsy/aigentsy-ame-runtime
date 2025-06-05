FROM python:3.10-slim

WORKDIR /app

COPY . .

# ✅ Force exact versions — guaranteed clean combo
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
      langchain==0.1.13 \
      langchain-openai==0.1.2 \
      openai==1.30.1 \
      langgraph==0.0.40 \
      fastapi==0.110.0 \
      uvicorn==0.29.0 \
      pydantic==1.10.13

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
