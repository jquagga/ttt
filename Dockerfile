# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:020b5f4d7c9e5c8984bb33fbec815111dd3cf31090f37ec831044b5bc6b8505e

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
