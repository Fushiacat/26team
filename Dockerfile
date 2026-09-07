FROM python:3.11-slim
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
RUN useradd --create-home appuser
WORKDIR /app
RUN chown appuser:appuser /app
COPY --chown=appuser:appuser requirements.txt requirements.txt
ENV PATH="/home/appuser/.local/bin:${PATH}"
RUN pip install --no-cache-dir --user -r requirements.txt
COPY --chown=appuser:appuser . .
USER appuser
CMD ["python", "main.py"]