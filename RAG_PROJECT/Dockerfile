FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .

# 提前安装构建依赖
RUN pip install --upgrade pip setuptools wheel -i https://pypi.tuna.tsinghua.edu.cn/simple && \
    pip install --no-build-isolation --no-cache-dir -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt

COPY . .

CMD ["python", "app.py"]
