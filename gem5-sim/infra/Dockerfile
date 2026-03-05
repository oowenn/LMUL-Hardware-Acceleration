# Docker image for gem5 with LMUL accelerator model.
# Mirrors infra/Singularity.def for use where Docker is preferred (e.g. local dev, CI).

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    LC_ALL=C.UTF-8 \
    LANG=C.UTF-8 \
    PATH=/usr/local/bin:/usr/bin:/bin:${PATH}

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        make \
        git \
        wget \
        curl \
        ca-certificates \
        gzip \
        m4 \
        scons \
        pkg-config \
        python3 \
        python3-pip \
        python3-dev \
        python3-venv \
        zlib1g-dev \
        libprotobuf-dev \
        protobuf-compiler \
        libprotoc-dev \
        libpng-dev \
        libhdf5-dev \
        libgoogle-perftools-dev \
        libboost-all-dev \
        gcc-arm-linux-gnueabihf \
        libc6-dev-armhf-cross \
        binutils-gold && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m pip install --upgrade pip setuptools wheel && \
    pip3 install --no-cache-dir \
        scons \
        numpy \
        matplotlib \
        pandas \
        scipy \
        jupyter \
        jupyterlab \
        ipykernel

# Default working directory when repo is mounted here
WORKDIR /workspace

LABEL org.opencontainers.image.title="gem5 LMUL Accelerator"
LABEL org.opencontainers.image.description="Container for gem5 simulator with LMUL accelerator model"
LABEL org.opencontainers.image.version="1.0"
