# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:b4611c2622b0f7550ea4b1fce1887a75e8b7cbcf79b20cd6f1a3e4a0a484d8f7

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
