FROM python:3.10-slim

# Change to the directory
WORKDIR /app

# Set the stdout and stderr logged and also stops python from writing .pyc to disk
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Copy the requirments.txt to the app/requirements.tx 
COPY requirements.txt /app

# Install the dependencies needed
RUN apt-get update -y && \
    apt-get install -y netcat-traditional libpq-dev gcc

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r  requirements.txt

COPY .  /app/

RUN chmod +x /app/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/app/entrypoint.sh"]

CMD ["python3", "manage.py", "runserver", "0.0.0.0:8000"]