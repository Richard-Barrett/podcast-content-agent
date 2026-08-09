FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY . /app
RUN useradd -m appuser && chown -R appuser:appuser /app
USER appuser
ENTRYPOINT ["python", "-m", "app.main"]
CMD ["--input", "data/input", "--output", "outputs", "--kb", "kb/facts.json", "--logs", "logs"]
