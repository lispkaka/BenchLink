FROM node:18-alpine

WORKDIR /app

# 复制依赖文件
COPY frontend/package.json frontend/package-lock.json* ./

# 安装依赖
RUN npm install

# 复制项目文件
COPY frontend/ .

# 构建项目
RUN npm run build

# 使用 nginx 提供服务
FROM nginx:alpine
COPY --from=0 /app/dist /usr/share/nginx/html
COPY docker/nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]



