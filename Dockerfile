FROM python:3.10-slim

WORKDIR /app

COPY . .

# 💣 Blow away old packages, then install correct ones
RUN pip uninstall -y openai langchain langchain-openai || true && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --force-reinstall -r requirements.patched.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
