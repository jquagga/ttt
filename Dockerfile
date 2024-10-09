# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:3dba8347f0353511545b6983c072be92917961214c789956cef1d64c1c63477e

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
