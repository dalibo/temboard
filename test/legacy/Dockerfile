FROM centos:7

# Add the PostgreSQL PGP key to verify the official yum repository packages
RUN rpm --import \
    https://yum.postgresql.org/RPM-GPG-KEY-PGDG-94 \
    https://yum.postgresql.org/RPM-GPG-KEY-PGDG-95 \
    https://yum.postgresql.org/RPM-GPG-KEY-PGDG-96 \
    https://yum.postgresql.org/RPM-GPG-KEY-PGDG-10 \
    ${NULL-}

# Add PostgreSQL's repository.
RUN yum -q -y install \
    epel-release \
    https://download.postgresql.org/pub/repos/yum/9.4/redhat/rhel-7-x86_64/pgdg-centos94-9.4-3.noarch.rpm \
    https://download.postgresql.org/pub/repos/yum/9.5/redhat/rhel-7-x86_64/pgdg-centos95-9.5-3.noarch.rpm \
    https://download.postgresql.org/pub/repos/yum/9.6/redhat/rhel-7-x86_64/pgdg-centos96-9.6-3.noarch.rpm \
    https://download.postgresql.org/pub/repos/yum/testing/10/redhat/rhel-7-x86_64/pgdg-centos10-10-1.noarch.rpm \
    ${NULL-}

# Update the Fedora and PostgreSQL repository metadata
RUN yum -q -y install \
    procps-ng net-tools python python2-pip sudo \
    postgresql94-server postgresql94-contrib \
    postgresql95-server postgresql95-contrib \
    postgresql96-server postgresql96-contrib \
    postgresql10-server postgresql10-contrib \
    ${NULL-}

# Setup test env
RUN pip install pytest && \
    useradd --system testuser
