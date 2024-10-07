FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
COPY ./generate_config.sh /app/generate_config.sh
RUN chmod +x /app/generate_config.sh

RUN echo "0 7,14 * * * /app/cron_script.sh >> /var/log/cron.log 2>&1" | crontab -

ENTRYPOINT ["/app/generate_config.sh"]
CMD ["python", "main.py"]
