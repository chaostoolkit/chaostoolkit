FROM python:3.5-alpine

LABEL maintainer="chaostoolkit <contact@chaostoolkit.org>"

RUN pip install --no-cache-dir chaostoolkit

ENTRYPOINT ["/usr/local/bin/chaos"]
CMD ["--help"]