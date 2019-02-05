# What is this?
This project is based on Alpine Linux, the official nginx image and an nginx module that provides static and dynamic brotli compression. Brotli is built by Google. Originally this image used Google's nginx brotli module, though as it is no longer maintained I switched to [eustas' fork](https://github.com/eustas/ngx_brotli).

# How to use this image
As this project is based on the official [nginx image](https://hub.docker.com/_/nginx/) look for instructions there. In addition to the standard configuration directives, you'll be able to use the brotli module specific ones, see [here for official documentation](https://github.com/eustas/ngx_brotli#configuration-directives)
