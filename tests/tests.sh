if [ "x`whoami`" == "xroot" ]; then
	echo "Installing test dependencies..."
	apk update
	apk add git openssl ffmpeg uwsgi uwsgi-python perl perl-fcgi perl-gd perl-io-socket-ssl perl-net-ssleay perl-test-harness-utils
	su -s /bin/sh -c /tests.sh - nginx
else
	git clone https://github.com/nginx/nginx-tests.git
	cd nginx-tests
	ls -1 *.t | grep -v '^http_listen.t$' | TEST_NGINX_BINARY=/usr/sbin/nginx-debug TEST_NGINX_MODULES=/etc/nginx/modules TEST_NGINX_LEAVE=1 xargs prove
fi
