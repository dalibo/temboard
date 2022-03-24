default:

renew_sslca:
	openssl req -batch -x509 -new -nodes -key share/temboard_CHANGEME.key -sha256 -days 1095 -out share/temboard_ca_certs_CHANGEME.pem

renew_sslcert:
	openssl req -batch -new -key share/temboard_CHANGEME.key -out request.pem
	openssl x509 -req -in request.pem -CA share/temboard_ca_certs_CHANGEME.pem -CAkey share/temboard_CHANGEME.key -CAcreateserial -sha256 -days 1095 -out share/temboard_CHANGEME.pem
	rm -f request.pem share/temboard_ca_certs_CHANGEME.srl
