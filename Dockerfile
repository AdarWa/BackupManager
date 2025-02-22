FROM python:3-slim

EXPOSE 5678

# Keeps Python from generating .pyc files in the container
ENV PYTHONDONTWRITEBYTECODE=1

# Turns off buffering for easier container logging
ENV PYTHONUNBUFFERED=1

# Install pip requirements
COPY requirements.txt .
RUN python -m pip install -r requirements.txt

WORKDIR /app
COPY . /app


# RUN adduser -u 5678 --disabled-password --gecos "" appuser && chown -R appuser /app && chmod -R 777 /app
# RUN chmod 777 /var/run/docker.sock && chown appuser /var/run/docker.sock

# USER appuser

CMD ["gunicorn", "--bind", "0.0.0.0:5678", "main:app"]
