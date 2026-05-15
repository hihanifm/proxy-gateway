ARG PYTHON_IMAGE=public.ecr.aws/docker/library/python:3.11-slim
FROM ${PYTHON_IMAGE}

ARG HTTP_PROXY
ARG HTTPS_PROXY
ARG NO_PROXY
ENV HTTP_PROXY=${HTTP_PROXY} HTTPS_PROXY=${HTTPS_PROXY} NO_PROXY=${NO_PROXY}

WORKDIR /app
COPY requirements.txt .

# Install offline from pip-cache if wheels are present (bind-mount keeps them
# out of the image layer so the cache is only busted by requirements.txt changes,
# not by pip-cache/ content changes); fall back to PyPI for lab proxy environments.
RUN --mount=type=bind,source=pip-cache,target=/tmp/pip-cache \
    if ls /tmp/pip-cache/*.whl /tmp/pip-cache/*.tar.gz 2>/dev/null | grep -q .; then \
      pip install --no-index --find-links /tmp/pip-cache/ -r requirements.txt; \
    else \
      pip install \
        --trusted-host pypi.org \
        --trusted-host pypi.python.org \
        --trusted-host files.pythonhosted.org \
        -r requirements.txt; \
    fi

COPY gateway/ ./gateway/
CMD ["uvicorn", "gateway.main:app", "--host", "0.0.0.0", "--port", "8000"]
