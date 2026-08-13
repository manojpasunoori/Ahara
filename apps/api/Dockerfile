FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app
RUN addgroup --system ahara && adduser --system --ingroup ahara ahara
COPY pyproject.toml ./
COPY app ./app
RUN pip install --upgrade pip && pip install .

USER ahara
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]