ARG DOCKER_MIRROR=docker.m.daocloud.io
FROM ${DOCKER_MIRROR}/library/python:3.11-slim

ARG PIP_INDEX_URL=https://pypi.tuna.tsinghua.edu.cn/simple
ARG PIP_TRUSTED_HOST=pypi.tuna.tsinghua.edu.cn

WORKDIR /app

COPY requirements.txt .
RUN pip config set global.index-url "${PIP_INDEX_URL}" \
    && pip config set global.trusted-host "${PIP_TRUSTED_HOST}" \
    && pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 5000
CMD ["python", "data_api.py"]
