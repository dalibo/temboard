DISTDIR=../../dist

default:

build-%:
	mkdir -p $(DISTDIR)
	env -u COMPOSE_FILE docker compose run -e CLEAN --rm $*
