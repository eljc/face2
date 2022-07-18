FROM nginx:1.19-alpine

RUN rm /etc/nginx/conf.d/default.conf
COPY nginx.conf /etc/nginx/nginx.conf
COPY my-site.crt /etc/ssl/certs/my-site.crt
COPY my-site1.key /etc/ssl/private/my-site.key
COPY global.pass /etc/ssl/certs/global.pass 

# copy project
COPY . /usr/src/app/