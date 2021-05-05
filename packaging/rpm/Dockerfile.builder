# -*- dockerfile -*-
FROM rpmbuild/centos7
USER root
RUN yum install -y epel-release && \
    yum install -y python3 python3-pip python3-rpm-macros python3-setuptools && \
    yum clean all
USER builder

ENV FLAVOR=rpmbuild OS=centos DIST=el7
CMD /srv/pkg
