FROM python:3-slim-bullseye AS build-venv

ARG DEBIAN_FRONTEND=noninteractive
ARG CTK_VERSION

RUN groupadd -g 1001 ctk && useradd -r -u 1001 -g ctk ctk

ADD requirements.txt requirements.txt
RUN apt-get update && \
    apt-get install -y --no-install-recommends build-essential gcc && \
    python3 -m venv /home/svc/.venv && \
    /home/svc/.venv/bin/pip install --no-cache-dir -q -U --disable-pip-version-check --prefer-binary pip && \
    /home/svc/.venv/bin/pip install --no-cache-dir -q --prefer-binary setuptools wheel && \
    /home/svc/.venv/bin/pip install --no-cache-dir --prefer-binary chaostoolkit==${CTK_VERSION} && \
    chown --recursive ctk:ctk /home/svc && \
    apt-get remove -y build-essential gcc && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

FROM python:3-slim-bullseye

LABEL org.opencontainers.image.authors="chaostoolkit <contact@chaostoolkit.org>"
LABEL org.opencontainers.image.vendor="Chaos Toolkit"
LABEL org.opencontainers.image.url="https://chaostoolkit.org"
LABEL org.opencontainers.image.source="https://gtihub.com/chaostoolkit/chaostoolkit/container/Dockerfile"
LABEL org.opencontainers.image.licenses="Apache-2.0"

RUN groupadd -g 1001 svc && useradd -r -u 1001 -g svc svc
COPY --from=build-venv --chown=svc:svc /home/svc /home/svc/
RUN ln -s /home/svc/.venv/bin/chaos /usr/local/bin/chaos

WORKDIR /home/svc
USER 1001
ENV PATH="/home/svc/.venv/bin:${PATH}" 

ENTRYPOINT ["chaos"]
CMD ["--help"]
