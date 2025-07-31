FROM python:3.12-slim

WORKDIR /app

# 拷贝依赖文件并安装
COPY requirements.txt .

# 安装依赖和 gunicorn（使用清华源）
RUN pip install --upgrade pip setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-build-isolation --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt


# 拷贝应用代码
COPY . .

# 使用 gunicorn 启动 Flask 应用，监听 8001
CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:8001", "--timeout", "3000", "app:app"]

