FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
ENV BOT_TOKEN=ваш_токен
ENV ADMIN_ID=433698201
ENV WEBHOOK_URL=https://your-cloud-run-url.a.run.app

CMD ["python", "main.py"]
