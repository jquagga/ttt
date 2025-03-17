# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:5247f7fe17ceb08f0d874444793b7650dca78f976843d4ad533d7ff419431873

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
