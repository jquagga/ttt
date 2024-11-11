# trunk-ignore-all(checkov/CKV_DOCKER_2)
FROM debian:bookworm-slim@sha256:36e591f228bb9b99348f584e83f16e012c33ba5cad44ef5981a1d7c0a93eca22

# trunk-ignore(hadolint/DL3008)
RUN apt-get update && apt-get install -y --no-install-recommends ca-certificates build-essential software-properties-common git curl \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

#Nvidia
# trunk-ignore(hadolint/DL3008)
RUN curl -O https://developer.download.nvidia.com/compute/cuda/repos/debian12/x86_64/cuda-keyring_1.1-1_all.deb \
&& dpkg -i cuda-keyring_1.1-1_all.deb \
&& add-apt-repository contrib\
&& apt-get update\
&& apt-get -y install --no-install-recommends cuda-toolkit-12-6 nvidia-open \
&& apt-get clean \
&& rm -rf /var/lib/apt/lists/*

ENV PATH=/usr/local/cuda-12.6/bin${PATH:+:${PATH}}
ENV LD_LIBRARY_PATH=/usr/local/cuda-12.6/lib64${LD_LIBRARY_PATH:+:${LD_LIBRARY_PATH}}
ARG CUDA_VERSION=12.6
ARG CUDA_DOCKER_ARCH=compute_75

RUN git clone https://github.com/ggerganov/whisper.cpp.git /whisper
WORKDIR /whisper

# This pins the version and builds server
RUN GGML_CUDA=1 make -j server medium.en
# And this downloads the model.  If you change it, be sure and change the entrypoint
# line below to reference it.
#RUN /whisper/models/download-ggml-model.sh medium.en

USER nobody

#ENTRYPOINT ["/bin/bash"]
ENTRYPOINT ["/whisper/server", "--host", "0.0.0.0", "-m", "/whisper/models/ggml-medium.en.bin"]