FROM python:3.10-slim

# Change to the directory
WORKDIR /app

# Set the stdout and stderr logged and also stops python from writing .pyc to disk
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install the dependencies needed
RUN pip install --upgrade pip \
    && apt-get update apt-get install -y libpq-dev gcc

# Copy the requirments.txt to the app/requirements.tx 
COPY requirements.txt /app/requirements.txt

RUN pip install -r --no-cache requirements.txt

COPY .  /app/

EXPOSE 8000

CMD ['python3' 'manage.py' 'runserver' '0.0.0.0:8000']