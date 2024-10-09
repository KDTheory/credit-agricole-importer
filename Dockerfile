FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN apt-get update && apt-get install -y cron

COPY . .
COPY ./entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh
COPY ./generate_config.sh /app/generate_config.sh
RUN chmod +x /app/generate_config.sh
RUN /app/generate_config.sh

ENTRYPOINT ["/app/generate_config.sh"]
CMD ["/entrypoint.sh"]
# CMD ["python", "main.py"]
