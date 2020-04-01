ARG JANUS_VERSION
FROM bredfern/docker-janus:$JANUS_VERSION

WORKDIR /opt/janus-postprocess

RUN apt-get update -y && apt-get install -y python3-pip mkvtoolnix && rm -rf /var/lib/apt/lists/*
ADD ./requirements.txt ./requirements.txt
RUN pip3 install -r requirements.txt
ADD postprocess.py ./

ARG BUILD_DATE
ARG VCS_REF
LABEL org.label-schema.description="This image contains the videoroom mjr -> webm post-processor" \
  org.label-schema.docker.cmd="\
  docker run -d \
  --name <container-name> \
  <image-name> --rabbitmq-address <rabbitmq-address>" \
  org.label-schema.docker.debug="docker run <image-name> --help" \
  org.label-schema.docker.debug="docker exec -it <container-name> bash" \
  org.label-schema.name="olp-janus/post-process" \
  org.label-schema.vcs-url="https://gitlab.drakephx.com/development/nextgen/olp-janus/" \
  org.label-schema.vendor="Kryterion" \
  org.label-schema.schema-version="1.0.0" \
  org.label-schema.build-date=$BUILD_DATE \
  org.label-schema.vcs-ref=$VCS_REF \
  com.kryterion.olp-janus.janus-version=$JANUS_VERSION

ENTRYPOINT ["python3", "postprocess.py"]
CMD ["--help"]
