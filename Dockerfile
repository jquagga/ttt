# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:e958b6f1aaa0cb58e424da03127259edd87856871b815efe771d4c0928073d19

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app
# This is the arrdn filter model hogwash for ffmpeg noise reduction
copy sh.rnnn /app
COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
