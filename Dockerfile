# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:8a9a539f9a789805f2283719d29fb0afec012836b9a916d465e0c8f804ed927e

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app
# This is the arrdn filter model hogwash for ffmpeg noise reduction
copy sh.rnnn /app
COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
