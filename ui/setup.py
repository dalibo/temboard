import os

from setuptools import find_packages, setup

# Load version number
__version__ = None
setup_path = os.path.dirname(os.path.realpath(__file__))
exec(open(os.path.join(setup_path, "temboardui", "version.py")).read())

setup(
    name="temboard",
    version=__version__,
    description="temBoard User Interface.",
    long_description=open("README.md", encoding="utf-8").read(),
    long_description_content_type="text/markdown",
    packages=find_packages(),
    author="Dalibo",
    author_email="contact@dalibo.com",
    license="PostgreSQL",
    url="https://labs.dalibo.com/temboard",
    classifiers=[
        "Intended Audience :: System Administrators",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3.6",
        "Topic :: Database :: Database Engines/Servers",
        "Topic :: System :: Monitoring",
    ],
    python_requires="~=3.6",
    install_requires=[
        "cryptography"
        # There is no hard dependency on psycopg2 to allow using
        # psycopg2-binary instead. psycopg2 is not provided by psycopg2-binary
        # and there is no way to state an OR dependency in Python. It's up to
        # the user or package manager to ensure psycopg2 dependency. See
        # documentation.
    ],
    include_package_data=True,
    zip_safe=False,
    data_files=[
        (
            "share/temboard",
            [
                "share/auto_configure.sh",
                "share/create_repository.sh",
                "share/postinst.sh",
                "share/preun.sh",
                "share/purge.sh",
                "vendor.txt",
            ],
        ),
        (
            "share/temboard/sql/",
            [
                "share/sql/dev-fixture.sql",
                "share/sql/upgrade-monitoring-purge-instances.sql",
                "share/sql/reassign.sql",
            ],
        ),
        (
            "share/temboard/quickstart/",
            [
                "share/temboard_CHANGEME.key",
                "share/temboard_CHANGEME.pem",
                "share/temboard_ca_certs_CHANGEME.pem",
                "share/temboard.conf",
            ],
        ),
        ("lib/systemd/system", ["packaging/temboard.service"]),
    ],
    entry_points={
        "console_scripts": ["temboard = temboardui.__main__:main"],
        "temboardui.plugins": [
            "activity = temboardui.plugins.activity:ActivityPlugin",
            "dashboard = temboardui.plugins.dashboard:DashboardPlugin",
            "maintenance = temboardui.plugins.maintenance:MaintenancePlugin",
            "monitoring = temboardui.plugins.monitoring:MonitoringPlugin",
            "pgconf = temboardui.plugins.pgconf:PGConfPlugin",
            "statements = temboardui.plugins.statements:StatementsPlugin",
        ],
    },
)
