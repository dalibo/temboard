#!/bin/bash -eux
#
# Install UI & agent from packages.
#

main() {
	local disttag pkgtype

	disttag="$(guess_disttag)"
	pkgtype="$(guess_pkg_type "$disttag")"

	mapfile -t pkgs < <(readlink -e agent/dist/temboard-agent*"$disttag"*".$pkgtype" ui/dist/temboard*"$disttag"*".$pkgtype")
	test "${#pkgs[@]}" -eq 2

	"install_$pkgtype" "${pkgs[@]}"

	temboard --version
	temboard-agent --version
}

guess_disttag() {
	. /etc/os-release

	case "$ID" in
		centos)
			echo "el${VERSION_ID}"
			;;
		rocky)
			echo "${PLATFORM_ID#platform:}"
			;;
		debian)
			echo "$VERSION_CODENAME"
			;;
		*)
			echo "Unsupported distribution $ID." >&2
			return 1
			;;
	esac
}

guess_pkg_type() {
	local disttag="$1"

	case "$disttag" in
		bookworm|bullseye|buster|stretch|jessie)
			echo deb
			;;
		el*)
			echo rpm
			;;
		*)
			echo "Unsupported distribution tag: $disttag." >&2
			return 1
			;;
	esac
}


install_rpm() {
	"$(type -p retry)" yum --quiet --assumeyes  install "$@"
}


install_deb() {
	apt-get --assume-yes --quiet update
	apt install --no-install-recommends --quiet --yes "$@"
}


main "$@"
