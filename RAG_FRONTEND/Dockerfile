# 构建阶段
FROM node:22-alpine AS builder

WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN npm run build

# 生产阶段，nginx 托管静态资源
FROM nginx:stable-alpine

# 复制构建好的静态资源到 nginx 默认路径
COPY --from=builder /app/dist /usr/share/nginx/html

# 直接启动 nginx
CMD ["nginx", "-g", "daemon off;"]
