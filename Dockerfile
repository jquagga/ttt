# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:df7aa876ee0f9c56afba7cd3c2ca2d6aace84689e7577a9ba91fa807deb89ef8

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
