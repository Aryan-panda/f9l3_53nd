FROM node:20-alpine AS builder

WORKDIR /app

COPY package*.json ./
RUN npm ci

COPY . ./
RUN npm run build

# Nginx unprivileged runtime
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html
EXPOSE 5173

# Replace default nginx config to serve on 5173 for consistency
RUN sed -i 's/80/5173/g' /etc/nginx/conf.d/default.conf

CMD ["nginx", "-g", "daemon off;"]
