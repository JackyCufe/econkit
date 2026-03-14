FROM python:3.11-slim

WORKDIR /app

# 安装系统依赖（中文字体支持）
RUN apt-get update && apt-get install -y \
    fonts-wqy-zenhei \
    fonts-wqy-microhei \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 复制项目文件
COPY . .

# 暴露端口
EXPOSE 7860

# 启动命令（HF Spaces 默认端口 7860）
CMD ["streamlit", "run", "app.py", \
     "--server.port=7860", \
     "--server.address=0.0.0.0", \
     "--server.headless=true", \
     "--server.fileWatcherType=none", \
     "--server.enableXsrfProtection=false", \
     "--server.enableCORS=false"]
