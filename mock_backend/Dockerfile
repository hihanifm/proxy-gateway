FROM python:3.11-slim
WORKDIR /app
RUN pip install --no-cache-dir "fastapi[standard]>=0.111" "uvicorn[standard]>=0.29"
COPY . /app/mock_backend
CMD ["uvicorn", "mock_backend.main:app", "--host", "0.0.0.0", "--port", "8001"]
