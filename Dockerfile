FROM python:3.9-slim-buster
WORKDIR /nexfon-cgg
COPY ./sources.list /etc/apt/sources.list
RUN apt update && \
apt install build-essential gettext -y && \
pip install pipenv && \
rm -rf /var/lib/apt/lists/*
COPY ./Pipfile /nexfon-cgg
RUN pipenv update
COPY . /nexfon-cgg
EXPOSE 8000
ENTRYPOINT ["pipenv", "run", "uwsgi", "--ini", "./docker/configs/uwsgi/uwsgi.ini"]
