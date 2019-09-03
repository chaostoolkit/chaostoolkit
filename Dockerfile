FROM python:3.5-alpine

LABEL maintainer="chaostoolkit <contact@chaostoolkit.org>"

RUN apk add --no-cache --virtual build-deps gcc g++ git libffi-dev linux-headers \
        python3-dev musl-dev && \
    pip install --no-cache-dir  -q -U pip && \
    pip install --no-cache-dir chaostoolkit && \
    apk del build-deps

ENTRYPOINT ["/usr/local/bin/chaos"]
CMD ["--help"]