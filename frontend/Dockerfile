ARG DOCKER_MIRROR=docker.m.daocloud.io

# Stage 1: Build
FROM ${DOCKER_MIRROR}/library/node:20-alpine AS build
WORKDIR /app
COPY package.json package-lock.json* ./
ARG NPM_REGISTRY=https://registry.npmmirror.com
RUN npm config set registry ${NPM_REGISTRY} && npm ci
COPY . .
ARG VITE_API_BASE_URL=
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}
RUN npm run build-only

# Stage 2: Serve
FROM ${DOCKER_MIRROR}/library/nginx:1.27-alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
