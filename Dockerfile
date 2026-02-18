FROM python:3.9-slim
WORKDIR /app
RUN pip install --no-cache-dir requests
COPY filter.py .
# 默认创建一个 data 目录防止报错
RUN mkdir -p /app/data
CMD ["python", "filter.py"]
