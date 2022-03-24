default:

renew_sslca:
	openssl req -batch -x509 -new -nodes -key share/temboard-agent_CHANGEME.key -sha256 -days 1095 -out share/temboard-agent_ca_certs_CHANGEME.pem

renew_sslcert:
	openssl req -batch -new -key share/temboard-agent_CHANGEME.key -out request.pem
	openssl x509 -req -in request.pem -CA share/temboard-agent_ca_certs_CHANGEME.pem -CAkey share/temboard-agent_CHANGEME.key -CAcreateserial -sha256 -days 1095 -out share/temboard-agent_CHANGEME.pem
	rm -f request.pem share/temboard-agent_ca_certs_CHANGEME.srl
