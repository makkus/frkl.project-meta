FROM debian:stable

RUN \
   apt update -y && \
   apt install -y wget git

COPY frkl-project /usr/bin/frkl-project

RUN \
   chmod +x /usr/bin/frkl-project
