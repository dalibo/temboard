%global pkgname temboard
%global confdir %{_sysconfdir}/%{pkgname}
%global pkgversion 0.0.1
%global pkgrevision 1

%{!?python_sitelib: %global python_sitelib %(%{__python} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:		%{pkgname}
Version:        %{pkgversion}
Release:        %{pkgrevision}%{?dist}
Summary:	Temboard Web Interface

Group:		Applications/Databases
License:	BSD
URL:		http://tembord.io/
Source0:	%{pkgname}-%{version}.tar.gz
Source1:	temboard.init
Source2:	temboard.service
Patch1:		temboardui.plugins.supervision.model.orm.py.patch
BuildArch:	noarch
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)

BuildRequires:	python-setuptools

Requires:	python-tornado >= 3.2
Requires:	python-sqlalchemy >= 0.9.8
Requires:	python-psycopg2

%description
Temboard is a monitoring and remote control solution for PostgreSQL
This packages holds the web user interface

%prep
%setup -q -n %{pkgname}-%{version}
%if 0%{?rhel} <= 6
%patch1 -p1
%endif

%build
%{__python} setup.py build

%pre
# We want a system user and group to run the tornado webapp
groupadd -r temboard >/dev/null 2>&1 || :
useradd -M -g temboard -r -d /var/empty/temboard -s /sbin/nologin \
	-c "Temboard Web UI" temboard >/dev/null 2>&1 || :

%post
# first install: register init script / service file
if [ $1 -eq 1 ]; then
  %if 0%{?rhel} <= 6
  chkconfig --add temboard
  %endif

  %if 0%{?rhel} >= 7
  /bin/systemctl daemon-reload >/dev/null 2>&1 || :
  %endif
fi

%preun
# unregister init script on unistall
%if 0%{?rhel} <= 6
if [ $1 -eq 0 ]; then
  chkconfig --del temboard
fi
%endif

%postun
# 
%if 0%{?rhel} >= 7
/bin/systemctl daemon-reload >/dev/null 2>&1 || :
%endif


%install
PATH=$PATH:%{buildroot}%{python_sitelib}/%{pkgname}
%{__python} setup.py install --root=%{buildroot}
# config file
%{__install} -d -m 755 %{buildroot}/%{_sysconfdir}
%{__install} -d -m 750 %{buildroot}/%{confdir}
%{__install} -m 640 %{buildroot}/usr/share/temboard/temboard.conf.sample %{buildroot}/%{confdir}/temboard.conf
# dummy ssl files
%{__install} -d -m 750 %{buildroot}/%{confdir}/ssl
%{__install} -m 640 %{buildroot}/usr/share/temboard/temboard_ca_certs_CHANGEME.pem %{buildroot}/%{confdir}/ssl/temboard_ca_certs_CHANGEME.pem
%{__install} -m 600 %{buildroot}/usr/share/temboard/temboard_CHANGEME.key %{buildroot}/%{confdir}/ssl/temboard_CHANGEME.key
%{__install} -m 640 %{buildroot}/usr/share/temboard/temboard_CHANGEME.pem %{buildroot}/%{confdir}/ssl/temboard_CHANGEME.pem
# init script
%if 0%{?rhel} <= 6
%{__install} -d %{buildroot}%{_initrddir}
%{__install} -m 755 %{SOURCE1} %{buildroot}%{_initrddir}/temboard
%endif

%if 0%{?rhel} >= 7
install -d %{buildroot}%{_unitdir}
install -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/temboard.service
%endif
# log directory
%{__install} -d %{buildroot}/var/log/temboard
# pidfile directory
%{__install} -d %{buildroot}/var/run/temboard

%files
%config(noreplace) %attr(-,temboard,temboard) %{confdir}
%{python_sitelib}/*
/usr/share/temboard/*
/usr/bin/temboard
/usr/bin/metric-aggregator
%attr(-,temboard,temboard) /var/log/temboard
%if 0%{?rhel} <= 6
%{_initrddir}/temboard
%endif

%if 0%{?rhel} >= 7
%{_unitdir}/temboard.service
%endif

%attr(-,temboard,temboard) /var/run/temboard

%changelog
* Fri Jul 15 2016 Nicolas Thauvin <nicolas.thauvin@dalibo.com> - 0.0.1-1
- Initial release
