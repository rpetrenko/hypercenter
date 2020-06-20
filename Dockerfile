FROM python:3.7
ENV PYTHONUNBUFFERED 1
ENV APP_HOME /backend
ENV PORT 8080

WORKDIR $APP_HOME

ADD requirements.txt $APP_HOME/
RUN pip install --upgrade pip && pip install -r requirements.txt
#COPY backend/ .

ENV URL_TO_BINARY=https://github.com/vmware/govmomi/releases/download/v0.22.1/govc_linux_amd64.gz
RUN curl -L $URL_TO_BINARY | gunzip > /usr/local/bin/govc
RUN chmod +x /usr/local/bin/govc
