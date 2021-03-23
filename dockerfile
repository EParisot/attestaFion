FROM python:3

RUN apt-get update -y
RUN apt-get install -yqq unzip curl wget build-essential libgl1-mesa-glx libgtk-3-dev

# install Firefox
ARG FIREFOX_VERSION=86.0.1
RUN wget -q https://download-installer.cdn.mozilla.net/pub/firefox/releases/$FIREFOX_VERSION/linux-x86_64/en-US/firefox-$FIREFOX_VERSION.tar.bz2 -O /tmp/firefox.tar.bz2 \
   && rm -rf /opt/firefox \
   && tar -C /opt -xjf /tmp/firefox.tar.bz2 \
   && rm /tmp/firefox.tar.bz2 \
   && mv /opt/firefox /opt/firefox-$FIREFOX_VERSION \
   && ln -fs /opt/firefox-$FIREFOX_VERSION/firefox /usr/bin/firefox \
   && apt-get install libdbus-glib-1-2

# install geckodriver
ARG GECKODRIVER_VERSION=0.29.0
RUN wget -q https://github.com/mozilla/geckodriver/releases/download/v$GECKODRIVER_VERSION/geckodriver-v$GECKODRIVER_VERSION-linux64.tar.gz -O /tmp/geckodriver.tgz \
    && tar zxf /tmp/geckodriver.tgz -C /usr/bin/ \
    && rm /tmp/geckodriver.tgz

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /attestaFion/requirements.txt

COPY . /attestaFion
WORKDIR /attestaFion

# upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN chmod -R 777 attestations

CMD gunicorn attestaFion:app --workers 1 --threads 1 --timeout 0 -b 0.0.0.0:8080