%global pkgname temboard
%global confdir %{_sysconfdir}/%{pkgname}
%{!?pkgversion: %global pkgversion 1.1}
%{!?pkgrevision: %global pkgrevision 1}

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:          %{pkgname}
Version:       %{pkgversion}
Release:       %{pkgrevision}%{?dist}
Summary:       temBoard Web Interface

Group:         Applications/Databases
License:       PostgreSQL
URL:           http://temboard.io/
Source0:       %{pkgname}-%{version}.tar.gz
BuildArch:     noarch
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: python-setuptools
Requires:      python-tornado >= 3.2
Requires:      python-sqlalchemy >= 0.9.8
Requires:      python-psycopg2
Requires:      python-dateutil >= 1.5
Requires:      openssl
Requires:      mailcap

%description
temBoard is a monitoring and remote control solution for PostgreSQL
This packages holds the web user interface

%prep
%setup -q -n %{pkgname}-%{version}

%build
%{__python} setup.py build

%pre
# Create system user now to let rpm chown %files.
if ! getent passwd temboard &>/dev/null ; then
  useradd \
    --system --user-group --shell /sbin/nologin \
    --home-dir /var/lib/temboard \
    --comment "temBoard Web UI" temboard &>/dev/null
fi

%post
systemctl daemon-reload &>/dev/null || :

if systemctl is-active temboard >&/dev/null ; then
	systemctl restart temboard
elif ! [ -f /etc/temboard/temboard.conf ] && [ -x /usr/share/temboard/auto_configure.sh ] ; then
	if ! /usr/share/temboard/auto_configure.sh ; then
		echo "Auto-configuration failed. Skipping." &>2
		error "See documentation for how to setup." &>2
	fi
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :

%install
PATH=$PATH:%{buildroot}%{python_sitelib}/%{pkgname}
%{__python} setup.py install --root=%{buildroot}
# config file
%{__install} -d -m 755 %{buildroot}/%{_sysconfdir}
%{__install} -d -m 750 %{buildroot}/%{confdir}
%{__install} -d -m 755 %{buildroot}/%{_sysconfdir}/logrotate.d
%{__install} -m 644 %{buildroot}/usr/share/temboard/quickstart/temboard.logrotate %{buildroot}/%{_sysconfdir}/logrotate.d/temboard
%{__install} -d %{buildroot}/var/log/temboard
%{__install} -d %{buildroot}/var/lib/temboard

%files
%config(noreplace) %attr(-,temboard,temboard) %{confdir}
%config(noreplace) %{_sysconfdir}/logrotate.d/temboard
%{python_sitelib}/*
/usr/share/temboard/*
/usr/bin/temboard
%attr(-,temboard,temboard) /var/log/temboard
%{_unitdir}/temboard.service

%attr(-,temboard,temboard) /var/lib/temboard

%changelog
* Wed Nov 8 2017 Julien Tachoires <julmon@gmail.com> - 1.1-1
- Handling /var/lib/temboard directory
- Auto-signed SSL certs.
- Usage of a dedicated temboard config. file

* Fri Jul 15 2016 Nicolas Thauvin <nicolas.thauvin@dalibo.com> - 0.0.1-1
- Initial release
