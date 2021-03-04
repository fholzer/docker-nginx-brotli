ARG NGINX_VERSION=1.19.7
ARG MAXMIND_VERSION=1.5.2
ARG NGX_BROTLI_COMMIT=9aec15e2aa6feea2113119ba06460af70ab3ea62
ARG PCRE_VERSION=8.44
ARG ZLIB_VERSION=1.2.11
#ARG QUICHE_VERSION=0.7.0
ARG CONFIG="\
		--prefix=/etc/nginx \
		--sbin-path=/usr/sbin/nginx \
		--modules-path=/usr/lib/nginx/modules \
		--conf-path=/etc/nginx/nginx.conf \
		--error-log-path=/var/log/nginx/error.log \
		--http-log-path=/var/log/nginx/access.log \
		--pid-path=/var/run/nginx.pid \
		--lock-path=/var/run/nginx.lock \
		--http-client-body-temp-path=/var/cache/nginx/client_temp \
		--http-proxy-temp-path=/var/cache/nginx/proxy_temp \
		--http-fastcgi-temp-path=/var/cache/nginx/fastcgi_temp \
		--http-uwsgi-temp-path=/var/cache/nginx/uwsgi_temp \
		--http-scgi-temp-path=/var/cache/nginx/scgi_temp \
		--user=nginx \
		--group=nginx \
		--with-pcre=/usr/src/pcre-${PCRE_VERSION} \
  		--with-pcre-jit \
  		--with-zlib=/usr/src/zlib-${ZLIB_VERSION} \
		--with-http_ssl_module \
		--with-http_realip_module \
		--with-http_addition_module \
		--with-http_sub_module \
		--with-http_dav_module \
		--with-http_flv_module \
		--with-http_mp4_module \
		--with-http_gunzip_module \
		--with-http_gzip_static_module \
		--with-http_random_index_module \
		--with-http_secure_link_module \
		--with-http_stub_status_module \
		--with-http_auth_request_module \
		--with-http_xslt_module=dynamic \
		--with-http_image_filter_module=dynamic \
		--with-http_geoip_module=dynamic \
		--with-http_perl_module=dynamic \
		--with-threads \
		--with-stream \
		--with-stream_ssl_module \
		--with-stream_ssl_preread_module \
		--with-stream_realip_module \
		--with-stream_geoip_module=dynamic \
		--with-http_slice_module \
		--with-mail \
		--with-mail_ssl_module \
		--with-compat \
		--with-file-aio \
		--with-http_v2_module \
		--with-http_v3_module \
  		--with-openssl=/usr/src/quiche/deps/boringssl \
  		--with-quiche=/usr/src/quiche \
		--add-module=/usr/src/ngx_brotli \
		--add-module=/usr/src/headers-more-nginx-module \
  		--add-module=/usr/src/njs/nginx \
  		--add-module=/usr/src/nginx_cookie_flag_module \
		--add-dynamic-module=/ngx_http_geoip2_module \
		--add-dynamic-module=/ngx_http_ipdb_module \
		--with-cc-opt=-Wno-error \
	"

FROM alpine:latest
LABEL maintainer="NGINX Docker Maintainers <docker-maint@nginx.com>"

ARG NGINX_VERSION
ARG NGX_BROTLI_COMMIT
ARG CONFIG
ARG MAXMIND_VERSION
ARG PCRE_VERSION
ARG ZLIB_VERSION
#ARG QUICHE_VERSION

RUN set -x \
  && apk add --no-cache --virtual .build-deps \
    alpine-sdk \
    perl \
  && git clone https://github.com/leev/ngx_http_geoip2_module /ngx_http_geoip2_module \
  && wget https://github.com/maxmind/libmaxminddb/releases/download/${MAXMIND_VERSION}/libmaxminddb-${MAXMIND_VERSION}.tar.gz \
  && tar xf libmaxminddb-${MAXMIND_VERSION}.tar.gz \
  && cd libmaxminddb-${MAXMIND_VERSION} \
  && ./configure \
  && make \
  && make check \
  && make install \
  && apk del .build-deps \
  && ldconfig || :


RUN \
	apk add --no-cache --virtual .build-deps \
		gcc \
		libc-dev \
		make \
		openssl-dev \
		pcre-dev \
		zlib-dev \
		linux-headers \
		curl \
		gnupg1 \
		libxslt-dev \
		gd-dev \
		geoip-dev \
		perl-dev \
		libmaxminddb \
		libmaxminddb-dev \
		json-c-dev \
	&& apk add --no-cache --virtual .brotli-build-deps \
		autoconf \
		libtool \
		automake \
		git \
		g++ \
		cmake\
  		go \
  		perl \
 		rust \
 		cargo \
  		patch 

COPY nginx.pub /tmp/nginx.pub

RUN \
	mkdir -p /usr/src/ngx_brotli \
	&& cd /usr/src/ngx_brotli \
	&& git init \
	&& git remote add origin https://github.com/google/ngx_brotli.git \
	&& git fetch --depth 1 origin $NGX_BROTLI_COMMIT \
	&& git checkout --recurse-submodules -q FETCH_HEAD \
	&& git submodule update --init --depth 1 \
	&& cd .. \
	&& wget -qO- https://ftp.pcre.org/pub/pcre/pcre-${PCRE_VERSION}.tar.gz | tar zxvf - \
  	&& wget -qO- http://zlib.net/zlib-${ZLIB_VERSION}.tar.gz | tar zxvf - \
  	&& git clone --depth=1 --recursive https://github.com/openresty/headers-more-nginx-module \
  	&& git clone --depth=1 --recursive https://github.com/nginx/njs \
  	&& git clone --depth=1 --recursive https://github.com/AirisX/nginx_cookie_flag_module \
  	&& git clone --depth=1 --recursive --branch quiche-nginx-1.19.7 https://github.com/marinelli/quiche \
	&& curl -fSL https://nginx.org/download/nginx-$NGINX_VERSION.tar.gz -o nginx.tar.gz \
	&& curl -fSL https://nginx.org/download/nginx-$NGINX_VERSION.tar.gz.asc  -o nginx.tar.gz.asc \
        && sha512sum nginx.tar.gz nginx.tar.gz.asc \
	&& export GNUPGHOME="$(mktemp -d)" \
	&& gpg --import /tmp/nginx.pub \
	&& gpg --batch --verify nginx.tar.gz.asc nginx.tar.gz \
	&& mkdir -p /usr/src \
	&& git clone https://github.com/peytonyip/ngx_http_ipdb_module.git /ngx_http_ipdb_module \
	&& tar -zxC /usr/src -f nginx.tar.gz

RUN \
	cd /usr/src/nginx-$NGINX_VERSION \
	&& patch -p01 < /usr/src/quiche/extras/nginx/nginx-1.19.7.patch \
	&& ./configure $CONFIG --with-debug --build="pcre-${PCRE_VERSION} zlib-${ZLIB_VERSION} quiche-$(git --git-dir=/usr/src/quiche/.git rev-parse --short HEAD) headers-more-nginx-module-$(git --git-dir=/usr/src/headers-more-nginx-module/.git rev-parse --short HEAD) njs-$(git --git-dir=/usr/src/njs/.git rev-parse --short HEAD) nginx_cookie_flag_module-$(git --git-dir=/usr/src/nginx_cookie_flag_module/.git rev-parse --short HEAD)" \
	&& make -j$(getconf _NPROCESSORS_ONLN) \
	&& mv objs/nginx objs/nginx-debug \
	&& mv objs/ngx_http_xslt_filter_module.so objs/ngx_http_xslt_filter_module-debug.so \
	&& mv objs/ngx_http_image_filter_module.so objs/ngx_http_image_filter_module-debug.so \
	&& mv objs/ngx_http_geoip_module.so objs/ngx_http_geoip_module-debug.so \
	&& mv objs/ngx_http_perl_module.so objs/ngx_http_perl_module-debug.so \
	&& mv objs/ngx_stream_geoip_module.so objs/ngx_stream_geoip_module-debug.so \
	&& ./configure $CONFIG --build="pcre-${PCRE_VERSION} zlib-${ZLIB_VERSION} quiche-$(git --git-dir=/usr/src/quiche/.git rev-parse --short HEAD)  headers-more-nginx-module-$(git --git-dir=/usr/src/headers-more-nginx-module/.git rev-parse --short HEAD) njs-$(git --git-dir=/usr/src/njs/.git rev-parse --short HEAD) nginx_cookie_flag_module-$(git --git-dir=/usr/src/nginx_cookie_flag_module/.git rev-parse --short HEAD)" \
	&& make -j$(getconf _NPROCESSORS_ONLN)

RUN \
	cd /usr/src/nginx-$NGINX_VERSION \
	&& make install \
	&& rm -rf /etc/nginx/html/ \
	&& mkdir /etc/nginx/conf.d/ \
	&& mkdir -p /usr/share/nginx/html/ \
	&& install -m644 html/index.html /usr/share/nginx/html/ \
	&& install -m644 html/50x.html /usr/share/nginx/html/ \
	&& install -m755 objs/nginx-debug /usr/sbin/nginx-debug \
	&& install -m755 objs/ngx_http_xslt_filter_module-debug.so /usr/lib/nginx/modules/ngx_http_xslt_filter_module-debug.so \
	&& install -m755 objs/ngx_http_image_filter_module-debug.so /usr/lib/nginx/modules/ngx_http_image_filter_module-debug.so \
	&& install -m755 objs/ngx_http_geoip_module-debug.so /usr/lib/nginx/modules/ngx_http_geoip_module-debug.so \
	&& install -m755 objs/ngx_http_perl_module-debug.so /usr/lib/nginx/modules/ngx_http_perl_module-debug.so \
	&& install -m755 objs/ngx_stream_geoip_module-debug.so /usr/lib/nginx/modules/ngx_stream_geoip_module-debug.so \
	&& strip /usr/sbin/nginx* \
	&& strip /usr/lib/nginx/modules/*.so \
	\
	&& apk add --no-cache --virtual .gettext gettext \
	\
	&& scanelf --needed --nobanner /usr/sbin/nginx /usr/lib/nginx/modules/*.so /usr/bin/envsubst \
			| awk '{ gsub(/,/, "\nso:", $2); print "so:" $2 }' \
			| sort -u \
			| xargs -r apk info --installed \
			| sort -u > /tmp/runDeps.txt

FROM alpine:latest
ARG NGINX_VERSION

COPY --from=0 /tmp/runDeps.txt /tmp/runDeps.txt
COPY --from=0 /etc/nginx /etc/nginx
COPY --from=0 /usr/lib/nginx/modules/*.so /usr/lib/nginx/modules/
COPY --from=0 /usr/sbin/nginx /usr/sbin/nginx-debug /usr/sbin/
COPY --from=0 /usr/share/nginx/html/* /usr/share/nginx/html/
COPY --from=0 /usr/bin/envsubst /usr/local/bin/envsubst

RUN \
	addgroup -S nginx \
	&& adduser -D -S -h /var/cache/nginx -s /sbin/nologin -G nginx nginx \
	&& apk add --no-cache --virtual .nginx-rundeps tzdata $(cat /tmp/runDeps.txt) \
	&& rm /tmp/runDeps.txt \
	&& ln -s /usr/lib/nginx/modules /etc/nginx/modules \
	# forward request and error logs to docker log collector
	&& mkdir /var/log/nginx \
	&& touch /var/log/nginx/access.log /var/log/nginx/error.log \
	&& ln -sf /dev/stdout /var/log/nginx/access.log \
	&& ln -sf /dev/stderr /var/log/nginx/error.log \
	&& rm -rf /usr/lib/perl5 \
    && rm -rf /usr/share/perl5

COPY nginx.conf /etc/nginx/nginx.conf
COPY nginx.vh.default.conf /etc/nginx/conf.d/default.conf

EXPOSE 80 443

STOPSIGNAL SIGTERM

CMD ["nginx", "-g", "daemon off;"]

