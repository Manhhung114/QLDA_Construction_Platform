FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY requirements.txt alembic.ini start.sh ./
RUN pip install --no-cache-dir -r requirements.txt
COPY alembic ./alembic
COPY app ./app
RUN chmod +x ./start.sh && mkdir -p /data/uploads
EXPOSE 8000
CMD ["./start.sh"]
