FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# `docker run -e OPENAI_API_KEY=... <image>` runs the job once and exits.
CMD ["python", "main.py"]
