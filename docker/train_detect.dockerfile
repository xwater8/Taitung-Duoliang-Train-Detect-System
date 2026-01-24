FROM python:3.10-slim
COPY ./docker/requirements.txt /git/requirements.txt
RUN pip3 install -r /git/requirements.txt


RUN apt-get update && apt-get install -y \
    tzdata \
    libgl1 \
    libglib2.0-0 \
    libxkbcommon-x11-0 \
    libxcb-xinerama0 \
    libxcb-xinput0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /workspace