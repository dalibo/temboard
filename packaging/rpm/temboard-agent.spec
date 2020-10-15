%global pkgname temboard-agent
%{!?pkgversion: %global pkgversion 1.1}
%{!?pkgrevision: %global pkgrevision 1}

Name:          %{pkgname}
Version:       %{pkgversion}
Release:       %{pkgrevision}%{?dist}
Summary:       temBoard agent

Group:         Applications/Databases
License:       PostgreSQL
URL:           http://temboard.io/
Source0:       %{pkgname}-%{version}.tar.gz
Source1:       temboard-agent.init
Source2:       temboard-agent.service
Source3:       temboard-agent.rpm.conf
BuildArch:     noarch
Requires:      openssl
Requires:      python3-setuptools
Requires:      python3-psycopg2
BuildRequires: python3-rpm-macros
BuildRequires: python3-setuptools

%description
Administration & monitoring PostgreSQL agent.


%prep
%setup -q -n %{pkgname}-%{version}


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
%{__install} -m 600 %{SOURCE3} %{buildroot}/%{_sysconfdir}/temboard-agent/temboard-agent.conf

# init script

%{__install} -d %{buildroot}%{_unitdir}
%{__install} -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/temboard-agent.service

# log directory
%{__install} -d %{buildroot}/var/log/temboard-agent
# work directory
%{__install} -d %{buildroot}/var/lib/temboard-agent/main
# pidfile directory
%{__install} -d %{buildroot}/var/run/temboard-agent
%{__install} -m 600 /dev/null %{buildroot}/%{_sysconfdir}/temboard-agent/users

%post
# auto-signed SSL cert. building
openssl req -new -x509 -days 365 -nodes -out /etc/pki/tls/certs/temboard-agent.pem -keyout /etc/pki/tls/private/temboard-agent.key -subj "/C=XX/ST= /L=Default/O=Default/OU= /CN= " >> /dev/null 2>&1
chmod 644 /etc/pki/tls/private/temboard-agent.key


if [ -x /usr/share/temboard-agent/restart-all.sh ] ; then
    /usr/share/temboard-agent/restart-all.sh
elif systemctl is-system-running &>/dev/null ; then
    systemctl daemon-reload
    if systemctl is-active temboard-agent &>/dev/null; then
        systemctl restart temboard-agent
    fi
fi

%files
%config(noreplace) %attr(-,postgres,postgres) %{_sysconfdir}/temboard-agent
%{python3_sitelib}/*
/usr/share/temboard-agent/*
/usr/bin/temboard-agent*

%{_unitdir}/temboard-agent*.service

%attr(-,postgres,postgres) /var/log/temboard-agent
%attr(-,postgres,postgres) /var/lib/temboard-agent
%config(noreplace) %attr(0600,postgres,postgres) /etc/temboard-agent/users

%preun
if systemctl is-system-running &>/dev/null ; then
    systemctl stop temboard-agent*
    systemctl disable $(systemctl --plain list-units temboard-agent* | grep -Po temboard-agent.*\\.service)
    systemctl reset-failed temboard-agent*
fi


%postun
if systemctl is-system-running &>/dev/null ; then
    systemctl daemon-reload
fi


%changelog
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
