# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:fd1ee87e695ac3b624405fbc38da40db1c5334bc2f64d03aa60adb9104e5bd4d

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
