# 第一阶段：构建基础镜像
FROM rust AS base
LABEL author daiqian <alexdai@vivo.com>

ENV RUSTUP_DIST_SERVER https://mirrors.tuna.tsinghua.edu.cn/rustup
ENV RUSTUP_UPDATE_ROOT https://mirrors.tuna.tsinghua.edu.cn/rustup/rustup

RUN rustup default stable && \
    rustup target add armv7a-none-eabi && \
    cargo install cargo-binutils && \
    rustup component add llvm-tools-preview && \
    rustup component add rust-src && \
    rustup component add rustfmt

ADD sources.list /etc/apt/
ADD config ~/.cargo/

RUN DEBIAN_FRONTEND=noninteractive apt-get update -y && \
    apt-get install -y git wget bzip2 \
    build-essential libncurses-dev cppcheck \
    gcc-arm-none-eabi gdb-arm-none-eabi binutils-arm-none-eabi qemu-system-arm \
    scons libclang-dev && \
    apt-get clean -y

# 安装 Python 3.12.3
RUN wget https://www.python.org/ftp/python/3.12.3/Python-3.12.3.tgz && \
    tar -xzf Python-3.12.3.tgz && \
    cd Python-3.12.3 && \
    ./configure --enable-optimizations && \
    make -j$(nproc) && \
    make altinstall && \
    cd .. && \
    rm -rf Python-3.12.3 Python-3.12.3.tgz


# 第二阶段：构建 c2rust 镜像
FROM base AS c2rust

RUN ln -sf /usr/local/bin/python3.12 /usr/bin/python3 && \
    ln -sf /usr/local/bin/pip3.12 /usr/bin/pip3

RUN DEBIAN_FRONTEND=noninteractive apt-get update && \
    apt-get install -y graphviz universal-ctags clang-14 libclang-14-dev cmake sudo && \
    apt-get clean -y

ENV PATH="/usr/bin:$PATH"
COPY requirements.txt /app/requirements.txt
RUN pip3 install --upgrade pip setuptools wheel && \
    pip3 install -r /app/requirements.txt

WORKDIR /root

CMD ["bash"]