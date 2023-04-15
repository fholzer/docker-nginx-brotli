if [ "x`whoami`" == "xroot" ]; then
	echo "Installing test dependencies..."
	apk update
	apk add mercurial openssl ffmpeg uwsgi uwsgi-python perl perl-fcgi perl-gd perl-io-socket-ssl perl-net-ssleay perl-test-harness-utils
	su -s /bin/sh -c /tests.sh - nginx
else
	hg clone http://hg.nginx.org/nginx-tests
	cd nginx-tests
	ls -1 *.t | grep -v '^http_listen.t$' | TEST_NGINX_BINARY=/usr/sbin/nginx-debug TEST_NGINX_MODULES=/etc/nginx/modules TEST_NGINX_LEAVE=1 xargs prove
fi
