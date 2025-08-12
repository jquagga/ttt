FROM ubuntu:oracular-20250619@sha256:cdf755952ed117f6126ff4e65810bf93767d4c38f5c7185b50ec1f1078b464cc AS ffmpeg-builder
RUN apt-get -y update && apt-get install -y --no-install-recommends wget xz-utils ca-certificates && \
	wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n7.1-latest-linux64-gpl-7.1.tar.xz && \
	tar xf ffmpeg-n7.1-latest-linux64-gpl-7.1.tar.xz && \
	mv ffmpeg-n7.1-latest-linux64-gpl-7.1/bin/ffmpeg /

# OpenVino based build with uv
FROM openvino/ubuntu24_runtime:2025.2.0@sha256:620845103dd304321d5d8818cbf4376c5054f7973f312eba2a2f8d88114dc383

COPY --from=ghcr.io/astral-sh/uv:latest@sha256:cda9608307dbbfc1769f3b6b1f9abf5f1360de0be720f544d29a7ae2863c47ef /uv /uvx /bin/

# Install the project into `/app`
WORKDIR /app

# Enable bytecode compilation
ENV UV_COMPILE_BYTECODE=1

# Copy from the cache instead of linking since it's a mounted volume
ENV UV_LINK_MODE=copy

# Install the project's dependencies using the lockfile and settings
RUN --mount=type=cache,target=/root/.cache/uv \
	--mount=type=bind,source=uv.lock,target=uv.lock \
	--mount=type=bind,source=pyproject.toml,target=pyproject.toml \
	uv sync --locked --no-install-project --no-dev

# Then, add the rest of the project source code and install it
# Installing separately from its dependencies allows optimal layer caching
COPY . /app
RUN --mount=type=cache,target=/root/.cache/uv \
	uv sync --locked --no-dev

# Place executables in the environment at the front of the path
ENV PATH="/app/.venv/bin:$PATH"

COPY --from=ffmpeg-builder /ffmpeg /app/.venv/bin/

CMD ["uv", "run", "ttt.py"]
