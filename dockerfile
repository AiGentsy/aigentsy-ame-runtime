FROM python:3.10-slim

WORKDIR /app

COPY . .

# 💣 Clear cache and force clean install
RUN pip uninstall -y openai langchain langchain-openai || true && \
    pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir --force-reinstall -r requirements.txt

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
