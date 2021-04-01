FROM docker.io/centos:8.3.2011

COPY provision.sh /provision.sh
RUN /provision.sh && rm /provision.sh

VOLUME /artifacts

COPY entrypoint.sh /entrypoint.sh
ENTRYPOINT ["/entrypoint.sh"]
