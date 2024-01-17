# What is this?
This project is based on Alpine Linux, the official nginx image and an nginx module that provides static and dynamic brotli compression. [Brotli](https://github.com/google/brotli) and the [nginx brotli module ](https://github.com/google/ngx_brotli) are built by Google.
This project also adds [GeoIP2](https://docs.nginx.com/nginx/admin-guide/dynamic-modules/geoip2/) module to NGINX to allow capturing information from the client IP address in variables, using the MaxMind GeoIP2 databases, with the GeoIP2 dynamic module.


# How to use this image
As this project is based on the official [nginx image](https://hub.docker.com/_/nginx/) look for instructions there. In addition to the standard configuration directives, you'll be able to use the brotli module specific ones, see [here for official documentation](https://github.com/google/ngx_brotli#configuration-directives)
