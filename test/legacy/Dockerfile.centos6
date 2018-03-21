FROM centos:6

RUN set -ex; \
    rpm --import https://yum.postgresql.org/RPM-GPG-KEY-PGDG-10; \
    yum -q -y install \
       epel-release \
       https://download.postgresql.org/pub/repos/yum/10/redhat/rhel-6-x86_64/pgdg-centos10-10-2.noarch.rpm \
    ; \
    yum -q -y install procps-ng net-tools sudo postgresql10-server postgresql10-contrib; \
    :

RUN yum -q -y install procps-ng net-tools python-logutils python-pip; \
    pip install "pytest<3.3"; \
    useradd --system testuser; \
    :
