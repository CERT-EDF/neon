FROM node:22 AS build
ARG GIT_TAG
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
RUN echo "export const version: string = '${GIT_TAG}';" > /app/public/version.ts
RUN npm run build

FROM nginx:alpine AS production
LABEL maintainer="github.com/cert-edf"
COPY nginx.conf /etc/nginx/nginx.conf
COPY --from=build /app/dist/*/browser /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
