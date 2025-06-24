# Build stage
FROM node:20-alpine AS build
WORKDIR /app

# Pass the API token and base URL as build arguments
ARG VITE_API_TOKEN
ENV VITE_API_TOKEN=${VITE_API_TOKEN}
ARG VITE_API_BASE_URL
ENV VITE_API_BASE_URL=${VITE_API_BASE_URL}

COPY package*.json ./
RUN rm -rf node_modules package-lock.json && npm install
COPY . .

RUN npm run build

# Serve stage
FROM nginx:alpine AS stage-1
WORKDIR /usr/share/nginx/html
RUN rm -rf ./*
COPY --from=build /app/dist .
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
ENTRYPOINT ["nginx", "-g", "daemon off;"] 