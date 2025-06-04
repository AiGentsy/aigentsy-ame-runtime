FROM python:3.10

WORKDIR /app

COPY . .

# Explicit install of required versions
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir \
        langchain==0.1.14 \
        langchain-openai==0.0.7 \
        openai==1.18.0 \
        langgraph==0.0.25 \
        fastapi==0.110.1 \
        uvicorn==0.29.0

CMD ["python", "main.py"]
