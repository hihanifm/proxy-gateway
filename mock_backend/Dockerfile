ARG PYTHON_IMAGE=public.ecr.aws/docker/library/python:3.11-slim
FROM ${PYTHON_IMAGE}

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV HTTP_PROXY=${HTTP_PROXY} HTTPS_PROXY=${HTTPS_PROXY} NO_PROXY=${NO_PROXY}

WORKDIR /app
COPY mock_backend/requirements.txt .
COPY pip-cache/ /tmp/pip-cache/

RUN --mount=type=cache,target=/root/.cache/pip \
    if ls /tmp/pip-cache/*.whl /tmp/pip-cache/*.tar.gz 2>/dev/null | grep -q .; then \
      pip install --no-index --find-links /tmp/pip-cache/ -r requirements.txt; \
    else \
      pip install \
        --trusted-host pypi.org \
        --trusted-host pypi.python.org \
        --trusted-host files.pythonhosted.org \
        -r requirements.txt; \
    fi

COPY mock_backend/ ./mock_backend/
CMD ["uvicorn", "mock_backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
