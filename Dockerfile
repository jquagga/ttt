# micromaba

FROM ghcr.io/mamba-org/micromamba:latest@sha256:921132dfafb8e64f59b69832c4061dcc7a7c6a00ee5ea39e1f2135c304758a47

COPY --chown=$MAMBA_USER:$MAMBA_USER environment.yml /tmp/environment.yml
RUN micromamba install -y -n base -f /tmp/environment.yml && \
    micromamba clean --all --yes

ARG MAMBA_DOCKERFILE_ACTIVATE=1
WORKDIR /app

COPY ttt.py /app

ENTRYPOINT ["/usr/local/bin/_entrypoint.sh", "python","-u","/app/ttt.py" ]
