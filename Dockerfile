# micromaba with cuda 11.8
FROM ghcr.io/mamba-org/micromamba:jammy-cuda-11.8.0@sha256:de6a267fa23fe806560c4b29d8d7106e1f87151d8e1b2043b2f0cf6851985195
COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
COPY --chown=$MAMBA_USER:$MAMBA_USER requirements.txt /tmp/requirements.txt
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app
COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
