%global pkgname temboard
%global confdir %{_sysconfdir}/%{pkgname}
%{!?pkgversion: %global pkgversion 1.1}
%{!?pkgrevision: %global pkgrevision 1}

%global __python /usr/bin/python3

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
%if 0%{?rhel} < 8
BuildRequires: python36-setuptools
Requires:      python36-cryptography
Requires:      python36-dateutil
Requires:      python36-flask
Requires:      python36-future
Requires:      python36-psycopg2
Requires:      python36-setuptools
Requires:      python36-sqlalchemy
Requires:      python36-tornado
%else
%if 0%{?rhel} < 9
BuildRequires: python36
%else
BuildRequires: python3
%endif
BuildRequires: python3-setuptools
BuildRequires: python3-rpm-macros
Requires:      python3-cryptography
Requires:      python3-dateutil >= 1.5
Requires:      python3-flask
Requires:      python3-future
Requires:      python3-psycopg2
Requires:      python3-setuptools
Requires:      python3-sqlalchemy >= 0.9.8
Requires:      python3-tornado
%endif
Requires:      openssl
Requires:      mailcap

%description
temBoard is a monitoring and remote control solution for PostgreSQL
This packages holds the web user interface

%prep
%setup -q -n %{pkgname}-%{version}

%build
%{__python} setup.py build

%post
systemctl daemon-reload &>/dev/null || :

if systemctl is-active temboard >&/dev/null ; then
	systemctl restart temboard
fi

%postun
/bin/systemctl daemon-reload >/dev/null 2>&1 || :

%install
PATH=$PATH:%{buildroot}%{python_sitelib}/%{pkgname}
%{__python} setup.py install --root=%{buildroot}
# config file
%{__install} -d -m 755 %{buildroot}/%{_sysconfdir}
%{__install} -d -m 750 %{buildroot}/%{confdir}

%files
%{python_sitelib}/*
/usr/share/temboard/*
/usr/bin/temboard
%{_unitdir}/temboard.service

%changelog
* Wed Nov 8 2017 Julien Tachoires <julmon@gmail.com> - 1.1-1
- Handling /var/lib/temboard directory
- Auto-signed SSL certs.
- Usage of a dedicated temboard config. file

* Fri Jul 15 2016 Nicolas Thauvin <nicolas.thauvin@dalibo.com> - 0.0.1-1
- Initial release
