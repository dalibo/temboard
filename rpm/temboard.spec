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
Source1:       temboard.service
Patch1:        temboard.conf.patch
BuildArch:     noarch
BuildRoot:     %{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires: python-setuptools
Requires:      python-tornado >= 3.2
Requires:      python-sqlalchemy >= 0.9.8
Requires:      python-psycopg2
Requires:      python-dateutil >= 1.5
Requires:      openssl
Requires:      temboard-sched

%description
temBoard is a monitoring and remote control solution for PostgreSQL
This packages holds the web user interface

%prep
%setup -q -n %{pkgname}-%{version}
%patch1 -p1

%build
%{__python} setup.py build


%pre
# We want a system user and group to run the tornado webapp
groupadd -r temboard >/dev/null 2>&1 || :
useradd -M -g temboard -r -d /var/empty/temboard -s /sbin/nologin \
    -c "temBoard Web UI" temboard >/dev/null 2>&1 || :


%post
# auto-signed SSL cert. building
openssl req -new -x509 -days 365 -nodes -out /etc/pki/tls/certs/temboard.pem -keyout /etc/pki/tls/private/temboard.key -subj "/C=XX/ST= /L=Default/O=Default/OU= /CN= " >> /dev/null 2>&1

# first install: register init script / service file
if [ $1 -eq 1 ]; then
  /bin/systemctl daemon-reload >/dev/null 2>&1 || :
fi


%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :


%install
PATH=$PATH:%{buildroot}%{python_sitelib}/%{pkgname}
%{__python} setup.py install --root=%{buildroot}
# config file
%{__install} -d -m 755 %{buildroot}/%{_sysconfdir}
%{__install} -d -m 750 %{buildroot}/%{confdir}
%{__install} -m 640 %{buildroot}/usr/share/temboard/quickstart/temboard.conf %{buildroot}/%{confdir}/temboard.conf
%{__install} -d -m 755 %{buildroot}/%{_sysconfdir}/logrotate.d
%{__install} -m 644 %{buildroot}/usr/share/temboard/quickstart/temboard.logrotate %{buildroot}/%{_sysconfdir}/logrotate.d/temboard

install -d %{buildroot}%{_unitdir}
install -m 644 %{SOURCE1} %{buildroot}%{_unitdir}/temboard.service

# log directory
%{__install} -d %{buildroot}/var/log/temboard
# home directory
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
