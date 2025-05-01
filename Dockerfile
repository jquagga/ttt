# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:ddd798c8a78d8e198cad33aa8c3a14d644d38fd3ceb4abd9d23686957f06de44

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
