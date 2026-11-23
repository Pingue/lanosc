FROM python:3.15-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY lanosc.py .
COPY games games

RUN useradd --uid 1000 --create-home app && mkdir /config
USER app

VOLUME /config
ENTRYPOINT ["python", "lanosc.py"]
CMD ["--config", "/config/lanosc.toml"]
