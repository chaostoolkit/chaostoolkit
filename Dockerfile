FROM python:3.5-alpine

LABEL maintainer="Sylvain Hellegouarch <sh@defuze.org>"

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir chaostoolkit

ENTRYPOINT ["/usr/local/bin/chaos"]
CMD ["--help"]