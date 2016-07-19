%global pkgname temboard-agent

%if 0%{?rhel} == 5
%define __python /usr/bin/python26
%endif

%{!?python_sitelib: %global python_sitelib %(%{__python2} -c "from distutils.sysconfig import get_python_lib; print (get_python_lib())")}

Name:		%{pkgname}
Version:        0.0.1
Release:        1%{?dist}
Summary:	Temboard agent

Group:		Applications/Databases
License:	BSD
URL:		http://temboard.io/
Source0:	%{pkgname}-%{version}.tar.gz
Source1:	temboard-agent.init
Source2:	temboard-agent.service
Patch1:		temboard-agent.conf.sample.patch
BuildArch:	noarch

%if 0%{?rhel} == 5
BuildRoot:	%{_tmppath}/%{name}-%{version}-%{release}-root-%(%{__id_u} -n)
BuildRequires:	python26-setuptools
%endif

%if 0%{?rhel} >= 6
BuildRequires:	python-setuptools
%endif

%description
Administration & monitoring PostgreSQL agent.


%prep
%setup -q -n %{pkgname}-%{version}
%patch1 -p1

%build
%{__python} setup.py build

%pre
# This comes from the PGDG rpm for PostgreSQL server. We want temboard to run
# under the same user as PostgreSQL
groupadd -g 26 -o -r postgres >/dev/null 2>&1 || :
useradd -M -n -g postgres -o -r -d /var/lib/pgsql -s /bin/bash \
        -c "PostgreSQL Server" -u 26 postgres >/dev/null 2>&1 || :

%install
PATH=$PATH:%{buildroot}%{python_sitelib}/%{pkgname}
%{__python} setup.py install --root=%{buildroot}
# config file
%{__install} -d -m 755 %{buildroot}/%{_sysconfdir}
%{__install} -d -m 750 %{buildroot}/%{_sysconfdir}/temboard-agent
%{__install} -m 640 %{buildroot}/usr/share/temboard-agent/temboard-agent.conf.sample %{buildroot}/%{_sysconfdir}/temboard-agent/temboard-agent.conf
# dummy ssl files
%{__install} -d -m 750 %{buildroot}/%{_sysconfdir}/temboard-agent/ssl
%{__install} -m 640 %{buildroot}/usr/share/temboard-agent/temboard-agent_ca_certs_CHANGEME.pem %{buildroot}/%{_sysconfdir}/temboard-agent/ssl/temboard-agent_ca_certs_CHANGEME.pem
%{__install} -m 600 %{buildroot}/usr/share/temboard-agent/temboard-agent_CHANGEME.key %{buildroot}/%{_sysconfdir}/temboard-agent/ssl/temboard-agent_CHANGEME.key
%{__install} -m 640 %{buildroot}/usr/share/temboard-agent/temboard-agent_CHANGEME.pem %{buildroot}/%{_sysconfdir}/temboard-agent/ssl/temboard-agent_CHANGEME.pem
# init script
%if 0%{?rhel} <= 6
%{__install} -d %{buildroot}%{_initrddir}
%{__install} -m 755 %{SOURCE1} %{buildroot}%{_initrddir}/temboard-agent
%endif

%if 0%{?rhel} >= 7
install -d %{buildroot}%{_unitdir}
install -m 644 %{SOURCE2} %{buildroot}%{_unitdir}/temboard-agent.service
%endif

# log directory
%{__install} -d %{buildroot}/var/log/temboard-agent
# work directory
%{__install} -d %{buildroot}/var/lib/temboard-agent/main
# pidfile directory
%{__install} -d %{buildroot}/var/run/temboard-agent

%files
%config(noreplace) %attr(-,postgres,postgres) %{_sysconfdir}/temboard-agent
#%config(noreplace) %attr(-,postgres,postgres) %{_sysconfdir}/temboard-agent/*
%{python_sitelib}/*
/usr/share/temboard-agent/*
/usr/bin/temboard-agent*
%if 0%{?rhel} <= 6
%{_initrddir}/temboard-agent
%endif

%if 0%{?rhel} >= 7
%{_unitdir}/temboard-agent.service
%endif

%attr(-,postgres,postgres) /var/log/temboard-agent
%attr(-,postgres,postgres) /var/lib/temboard-agent
%attr(-,postgres,postgres) /var/run/temboard-agent

%changelog
* Fri Jul  4 2016 Nicolas Thauvin <nicolas.thauvin@dalibo.com> - 0.0.1-1
- Initial release
