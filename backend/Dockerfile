FROM python:3.12-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PATH="/opt/venv/bin:$PATH"

RUN python -m venv /opt/venv \
    && addgroup --system policyflow \
    && adduser --system --ingroup policyflow --home /app policyflow

WORKDIR /app/backend
COPY --chown=policyflow:policyflow backend/requirements-runtime.txt ./requirements-runtime.txt
RUN pip install --no-cache-dir -r requirements-runtime.txt

COPY --chown=policyflow:policyflow backend/ ./
COPY --chown=policyflow:policyflow policies/synthetic/ /app/policies/synthetic/

USER policyflow
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=3)"

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers", "--forwarded-allow-ips=*"]
