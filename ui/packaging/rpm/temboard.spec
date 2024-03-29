%global pkgname temboard
%global confdir %{_sysconfdir}/%{pkgname}

%global __python /usr/bin/python3

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:          %{pkgname}
Version:       GENERATED
Release:       1%{?dist}
Summary:       PostgreSQL Remote Control - Web Interface

Group:         Applications/Databases
License:       PostgreSQL
URL:           https://labs.dalibo.com/temboard/
Source0:       %{pkgname}-%{version}.tar.gz
BuildArch:     noarch
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: python3-rpm-macros
BuildRequires: python3-setuptools
Requires:      mailcap
Requires:      openssl
Requires:      python3-flask
Requires:      python3-future
Requires:      python3-psycopg2
Requires:      python3-setuptools
Requires:      python3-tornado
%if 0%{?rhel} < 8
Requires:      python36-cryptography
Requires:      python36-dateutil
Requires:      python36-sqlalchemy < 2
%else
Requires:      python3-cryptography
Requires:      python3-dateutil >= 1.5
Requires:      python3-sqlalchemy >= 0.9.8, python3-sqlalchemy < 2
%endif

%description
temBoard is a monitoring and remote control solution for PostgreSQL.
This packages holds the web user interface.

%prep
%setup -q

%build
%{__python} setup.py build

%install
%{__python} setup.py install --root=%{buildroot}
# config file
%{__install} -d -m 755 %{buildroot}/%{_sysconfdir}
%{__install} -d -m 750 %{buildroot}/%{confdir}

%files
%{python_sitelib}/*
/usr/share/temboard/*
/usr/bin/temboard
%{_unitdir}/temboard.service

%post
/usr/share/temboard/postinst.sh "$@"

%preun
/usr/share/temboard/preun.sh "$@"

%verifyscript
# Smoketest with SMOKETEST=1 rpm -v --verify -p <rpm>
# This test is run by verify with *installed* package instead of in buildroot like %check.
if ! [ -v SMOKETEST ] ; then
    echo "Skipping smoketest." >&2
    exit 0
fi
temboard --version
test -f /usr/lib/python*/site-packages/temboardui/static/.vite/manifest.json

%changelog
* Fri Oct 14 2022 Dalibo Labs <contact@dalibo.com> - 8.0-1
- New Upstream Release

* Wed Nov 8 2017 Julien Tachoires <julmon@gmail.com> - 1.1-1
- Handling /var/lib/temboard directory
- Auto-signed SSL certs.
- Usage of a dedicated temboard config. file

* Fri Jul 15 2016 Nicolas Thauvin <nicolas.thauvin@dalibo.com> - 0.0.1-1
- Initial release
