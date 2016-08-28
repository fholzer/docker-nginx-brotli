# What is this?
This project is based on Alpine Linux, the official nginx image and an nginx module made by Google that provides brotli compression, which also is made by Google.

While the nginx module and the compression algorithm are made by Google, this project also relies on https://github.com/bagder/libbrotli to actually compile libbrotli in a way that nginx's configure script can find it. 

# How to use this image
As this project is based on the official [nginx image](https://hub.docker.com/_/nginx/) look for instructions there. In addition to the standard configuration directives, you'll be able to use the brotli module specific ones, see [here for official documentation](https://github.com/google/ngx_brotli#configuration-directives)
