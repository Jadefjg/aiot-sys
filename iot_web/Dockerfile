# 构建阶段
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json ./
RUN npm config set registry https://registry.npmmirror.com \
    && npm ci
COPY . .
RUN npm run build

# 运行阶段：Nginx 托管 SPA 并反代 API
FROM nginx:1.27-alpine
COPY nginx.docker.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html/iot
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
