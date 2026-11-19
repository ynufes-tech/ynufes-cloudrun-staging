FROM nginx:1.30.7-alpine@sha256:bef154735288bc38d99fac41ae63730684bcc661503673a04a0f9bc526ba8598

# Install the Alpine zlib security fix not yet included in the pinned base image.
RUN apk add --no-cache "zlib>=1.4-r0"

COPY default.conf /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/conf.d/nginx.conf
COPY www /var/www
#nginxを扱うためのdockerfile
CMD ["nginx", "-g", "daemon off;"]
