FROM sgrio/ubuntu-python:3

RUN apt-get update -y
RUN apt-get install -yqq unzip curl wget gnupg gnupg2 gnupg1

# install google chrome
#RUN wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
#RUN sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
#RUN apt-get -y update
#RUN apt-get install -y google-chrome-stable
RUN apt-get install -y chromium-browser

# install chromedriver
RUN wget -O /tmp/chromedriver.zip http://chromedriver.storage.googleapis.com/`curl -sS chromedriver.storage.googleapis.com/LATEST_RELEASE`/chromedriver_linux64.zip
RUN unzip /tmp/chromedriver.zip chromedriver -d /usr/local/bin/

# We copy just the requirements.txt first to leverage Docker cache
COPY ./requirements.txt /attestaFion/requirements.txt

COPY . /attestaFion
WORKDIR /attestaFion

# upgrade pip and install dependencies
RUN pip install --upgrade pip
RUN pip install -r requirements.txt

RUN chmod -R 777 attestations

CMD gunicorn attestaFion:app -b 0.0.0.0:8000