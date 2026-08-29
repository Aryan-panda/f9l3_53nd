# Multi-stage build for React/Vite web client
FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . ./
RUN npm run build

# Production runtime using unprivileged Nginx
FROM nginx:alpine

# Remove default configuration and copy custom secure config
RUN rm /etc/nginx/conf.d/default.conf
COPY ../infra/docker/nginx.conf /etc/nginx/conf.d/f9l3_frontend.conf

# Copy build artifacts
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 5173

HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
  CMD wget --quiet --tries=1 --spider http://localhost:5173/health || exit 1

CMD ["nginx", "-g", "daemon off;"]
