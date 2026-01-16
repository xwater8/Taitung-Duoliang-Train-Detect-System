FROM ubuntu:22.04

RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    && rm -rf /var/lib/apt/lists/*

# 根據架構自動下載 mediamtx（已更新下載網址格式）
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        URL="https://github.com/bluenviron/mediamtx/releases/download/v1.15.6/mediamtx_v1.15.6_linux_amd64.tar.gz"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        URL="https://github.com/bluenviron/mediamtx/releases/download/v1.15.6/mediamtx_v1.15.6_linux_arm64.tar.gz"; \
    else \
        echo "Unsupported architecture: $ARCH"; exit 1; \
    fi && \
    wget -O mediamtx.tar.gz "$URL" && \
    tar -xzf mediamtx.tar.gz && \
    mv mediamtx /usr/local/bin/mediamtx && \
    rm mediamtx.tar.gz

# 根據架構自動下載 yt-dlp（不使用 pip）
RUN ARCH=$(uname -m) && \
    if [ "$ARCH" = "x86_64" ]; then \
        URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux"; \
    elif [ "$ARCH" = "aarch64" ]; then \
        URL="https://github.com/yt-dlp/yt-dlp/releases/latest/download/yt-dlp_linux_aarch64"; \
    else \
        echo "Unsupported architecture: $ARCH"; exit 1; \
    fi && \
    wget -O /usr/local/bin/yt-dlp "$URL" && \
    chmod a+rx /usr/local/bin/yt-dlp

CMD ["mediamtx", "/mediamtx.yml"]