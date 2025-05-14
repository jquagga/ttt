# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:1d8da1e962933dae646f43d92c4b65a50204e64f688ecb74fa7e27e0d0694d2a

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
