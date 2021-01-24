FROM debian:stable

RUN \
   apt update -y && \
   apt install -y wget git

COPY project-meta /usr/bin/project-meta

RUN \
   chmod +x /usr/bin/project-meta
