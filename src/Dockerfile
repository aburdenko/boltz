FROM python:3.9-slim-buster

WORKDIR /boltz

# Install gcc and other necessary build tools
RUN apt-get update && apt-get install -y --no-install-recommends gcc libc6-dev 

COPY requirements.txt .


RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt

COPY ./boltz /boltz

# COPY the cache directory.
RUN mkdir -p /boltz/cache
# COPY the processed directory.
RUN mkdir -p /boltz/processed

ENV PYTHONPATH=/

EXPOSE 8080

#CMD ["python", "app.py"]

CMD ["gunicorn", "--bind", "0.0.0.0:8080", "app:app", "--workers", "3"]