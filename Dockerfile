FROM python:3.13-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all Python files in the directory
COPY *.py /app/

# Copy static web folder
COPY www /app/www

EXPOSE 8888

CMD ["python", "web-server.py"]
