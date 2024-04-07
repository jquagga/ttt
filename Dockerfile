# Mostly from: https://github.com/GoogleContainerTools/distroless/blob/main/examples/python3-requirements/Dockerfile
# Build a virtualenv using the appropriate Debian release

# FROM ubuntu:22.04@sha256:77906da86b60585ce12215807090eb327e7386c8fafb5402369e421f44eff17e AS build
# COPY requirements.txt /requirements.txt
# RUN apt-get update && apt-get install -y --no-install-recommends python3-venv && \
#     python3 -m venv /venv && \
#     /venv/bin/pip install --upgrade pip setuptools wheel && \
#     /venv/bin/pip install --no-cache-dir -r /requirements.txt

# Copy the virtualenv the nvidia cuda image
FROM nvidia/cuda:12.2.2-cudnn8-runtime-ubuntu22.04@sha256:2d913b09e6be8387e1a10976933642c73c840c0b735f0bf3c28d97fc9bc422e0
COPY requirements.txt /requirements.txt
RUN apt-get update && apt-get dist-upgrade -y && apt-get install -y --no-install-recommends python3-venv && apt-get clean all && \
    python3 -m venv /venv && \
    /venv/bin/pip install --upgrade pip setuptools wheel && \
    /venv/bin/pip install --no-cache-dir -r /requirements.txt
#COPY --from=build /venv /venv
WORKDIR /app
COPY ttt.py /app
ENTRYPOINT ["/venv/bin/python3","-u","/app/ttt.py"]
