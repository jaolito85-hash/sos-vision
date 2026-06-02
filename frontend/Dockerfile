# Build da Sala (Vite) + empacota os PWAs, servidos por nginx.
# IMPORTANTE: o contexto de build é a RAIZ do repo (precisa de ../pwa-*).
#   build: { context: ., dockerfile: frontend/Dockerfile }

FROM node:20-alpine AS build
ARG VITE_API
ENV VITE_API=$VITE_API
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM nginx:alpine
# Landing institucional na raiz (/); Sala em /sala; PWAs em /vitima e /campo.
COPY landing/ /usr/share/nginx/html/
COPY --from=build /app/dist /usr/share/nginx/html/sala/
COPY pwa-vitima/ /usr/share/nginx/html/vitima/
COPY pwa-campo/ /usr/share/nginx/html/campo/
COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
