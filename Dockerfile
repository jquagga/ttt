FROM ubuntu:oracular-20250428@sha256:707879280c0bbfe6cbeb3ae1a85b564ea2356b5310a122c225b92cb3d1ed131b AS ffmpeg-builder
RUN apt-get -y update && apt-get install -y --no-install-recommends wget xz-utils ca-certificates && \
	wget https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-n7.1-latest-linux64-gpl-7.1.tar.xz && \
	tar xf ffmpeg-n7.1-latest-linux64-gpl-7.1.tar.xz && \
	mv ffmpeg-n7.1-latest-linux64-gpl-7.1/bin/ffmpeg /

# OpenVino based build with uv
FROM openvino/ubuntu24_runtime:2025.1.0@sha256:001436f35f2660b24b7c984fb8a3fb6cf120bc7788abd222d955a662cd069572

COPY --from=ghcr.io/astral-sh/uv:latest@sha256:d7e699d374d4e5cb52a37d5c8f0ee15e3c7572850325953bf9fa8d781cfa92fc /uv /uvx /bin/

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
