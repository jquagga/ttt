# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:b17c9b1543a713d3a6cf48a0dc44a20ee26407ad75509fd28d86f6714dae8342

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
