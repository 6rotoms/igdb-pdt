FROM python:3.13.0a3

WORKDIR /script
ENV IGDB_SRC=MOCK
ENV REDIS_HOSTNAME=redis
COPY requirements.txt /script/requirements.txt
COPY data.json /script/data.json
COPY populate_db.py /script/populate_db.py
COPY startup.sh /script/startup.sh
RUN pip install --no-cache-dir -r requirements.txt

VOLUME /var/log
RUN apt-get update && apt-get -y install cron
COPY igdb-cron /etc/cron.d/igdb-cron
RUN chmod 0644 /etc/cron.d/igdb-cron
RUN touch /var/log/cron.log

CMD . /script/startup.sh
