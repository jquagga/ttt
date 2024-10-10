# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:c819f78646c1711add9176989ea5a1f4545f398523ebc48964ca0e1c9b3bd3e6

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
