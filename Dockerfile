FROM python:3.11.0rc2-slim-buster

WORKDIR /code
COPY requirements.txt /etc/

RUN apt-get clean && apt-get update && apt-get install -y gcc && \
    apt-get install -y make && \
    pip install -r /etc/requirements.txt \
                --no-cache-dir

COPY . .
COPY init.sh /code

# EXPOSE 8001

RUN chmod +x /code/init.sh
CMD ["python", "main.py"]
