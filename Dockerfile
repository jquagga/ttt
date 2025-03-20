# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:5955fa7ed20207a6f5e7e79c7f1815dc558b7b73d8d79145431d20ece01798eb

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
