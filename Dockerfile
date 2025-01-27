# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:ae98eaf47b2763e1fbddf730861f2c6378af6c2cba50e82473f5ecfb2e2aca62

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
