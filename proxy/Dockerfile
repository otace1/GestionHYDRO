FROM nginxinc/nginx-unprivileged:1.15


## Copy configuration files
#RUN rm /etc/nginx/conf.d/defaul.conf
COPY ./default.conf /etc/nginx/conf.d/default.conf
COPY ./uwsgi_params /etc/nginx/uwsgi_params

# Switch to root user to perform setup tasks
USER root

# Create directory for static files
RUN mkdir -p /vol/web/static && \
    chmod 755 /vol/web/static

# Switch back to non-root user
USER nginx

