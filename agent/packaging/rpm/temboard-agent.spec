%global pkgname temboard-agent

Name:          %{pkgname}
Version:       GENERATED
Release:       1%{?dist}
Summary:       PostgreSQL Remote Control - Agent Service

Group:         Applications/Databases
License:       PostgreSQL
URL:           https://labs.dalibo.com/temboard/
Source0:       %{pkgname}-%{version}.tar.gz
BuildArch:     noarch
BuildRequires: python3-rpm-macros
BuildRequires: python3-setuptools
Requires:      openssl
Requires:      python3-bottle
Requires:      python3-setuptools
Requires:      python3-psycopg2 >= 2.7
%if 0%{?rhel} < 8
Requires:      python36-cryptography
%else
Requires:      python3-cryptography
%endif

%description
temBoard agent monitor and operates on a PostgreSQL instance.
Requires a temBoard UI installation.

%prep
%setup -q

%build
%{__python3} setup.py build

%pre
# This comes from the PGDG rpm for PostgreSQL server. We want temboard to run
# under the same user as PostgreSQL
groupadd -g 26 -o -r postgres >/dev/null 2>&1 || :
useradd -M -n -g postgres -o -r -d /var/lib/pgsql -s /bin/bash \
        -c "PostgreSQL Server" -u 26 postgres >/dev/null 2>&1 || :


%install
%{__python3} setup.py install --root=%{buildroot}
# config file
%{__install} -d -m 755 %{buildroot}/%{_sysconfdir}
%{__install} -d -m 750 %{buildroot}/%{_sysconfdir}/temboard-agent

# init script

%{__install} -d %{buildroot}%{_unitdir}

# work directory
%{__install} -d %{buildroot}/var/lib/temboard-agent/main
# pidfile directory
%{__install} -d %{buildroot}/var/run/temboard-agent

%files
%config(noreplace) %attr(-,postgres,postgres) %{_sysconfdir}/temboard-agent
%{python3_sitelib}/*
/usr/share/temboard-agent/*
/usr/bin/temboard-agent*
%{_unitdir}/temboard-agent@.service
%attr(-,postgres,postgres) /var/lib/temboard-agent

%post
/usr/share/temboard-agent/restart-all.sh

%preun
/usr/share/temboard-agent/preun.sh "$@"

%verifyscript
temboard-agent --version >/dev/null


%changelog
* Fri Oct 14 2022 Dalibo Labs <contact@dalibo.com> - 8.0-1
- New Upstream Release

* Fri Oct  9 2020 Denis Laxalde <denis.laxalde@dalibo.com> - 7.1-2
- Build with Python 3 on CentOS/RHEL 7

* Fri Sep 25 2020 Pierre Giraud <pierre.giraud@dalibo.com>
- Remove centos6 support

* Wed Nov 8 2017 Julien Tachoires <julmon@gmail.com> - 1.1-1
- Handle systemd service on uninstall
- Build auto-signed SSL certs
- Set up users file as a config file
- Remove centos 5 support

* Mon Jul 4 2016 Nicolas Thauvin <nicolas.thauvin@dalibo.com> - 0.0.1-1
- Initial release
