from setuptools import setup

setup(
    name='temboard-agent-sample-plugins',
    version='1.0',
    author='Dalibo',
    author_email='contact@dalibo.com',
    license='PostgreSQL',
    install_requires=['temboard-agent'],
    py_modules=['temboard_agent_sample_plugins'],
    entry_points={
        'temboardagent.plugins': [
            'failing = temboard_agent_sample_plugins:Failing',
            'hellong = temboard_agent_sample_plugins:Hello',
            'inexistant = temboard_agent_sample_plugins:INEXISTANT',
        ],
    },
)
