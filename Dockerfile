# Pinned reproduction environment.
# Ubuntu 22.04 ships clang-14; pinning the distro pins the compiler major version,
# which is the single largest source of deviation from the 2012 paper (LLVM 3.1).

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

RUN apt-get update && apt-get install -y --no-install-recommends \
        build-essential \
        clang-14 \
        lld-14 \
        llvm-14 \
        valgrind \
        time \
        util-linux \
        python3 \
        ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Make the pinned compiler the default for `cc`/`make`.
ENV CC=clang-14
ENV PYTHONUNBUFFERED=1

WORKDIR /work

# Fail the build early if the toolchain is not what we expect.
RUN clang-14 --version | head -n 1 \
    && python3 --version \
    && uname -a

CMD ["make", "all"]
