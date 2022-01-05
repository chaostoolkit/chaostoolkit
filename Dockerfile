FROM python:3.7-alpine

LABEL maintainer="chaostoolkit <contact@chaostoolkit.org>"

ARG ctkversion

RUN apk add --no-cache --virtual build-deps gcc g++ git libffi-dev linux-headers \
        python3-dev musl-dev && \
    pip install --no-cache-dir -q -U pip setuptools && \
    pip install --no-cache-dir chaostoolkit==${ctkversion} && \
    apk del build-deps

RUN addgroup --gid 1001 svc
RUN adduser --disabled-password --home /home/svc --uid 1001 --ingroup svc svc
WORKDIR /home/svc

# Any non-zero number will do, and unfortunately a named user will not,
# as k8s pod securityContext runAsNonRoot can't resolve the user ID:
# https://github.com/kubernetes/kubernetes/issues/40958
USER 1001

ENTRYPOINT ["/usr/local/bin/chaos"]
CMD ["--help"]
