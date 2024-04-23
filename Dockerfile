# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:cca06974c6ff7641cc4ec15bcc60d0147084d9b9476fc61a06e7524891349a1f

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app
# This is the arrdn filter model hogwash for ffmpeg noise reduction
copy sh.rnnn /app
COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
