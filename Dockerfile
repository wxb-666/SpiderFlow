FROM python:3.11-slim

WORKDIR /app

# 安装依赖时关闭缓存，减小最终镜像体积。
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY scrapy.cfg ./
COPY spiderflow ./spiderflow
RUN mkdir -p /app/data

CMD ["python", "-m", "spiderflow.main"]
