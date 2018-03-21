# Sample External Plugins

This dumb project provides real external plugins to temboard agent.

Use it as following:

- Setup project with `python setup.py egg_info` in this directory.
- Enter the container and install the project with `pip install -e /usr/local/src/temboard-agent/test/temboard-agent-sample-plugins/`.
- Run the agent with plugins : `TEMBOARD_PLUGINS='["hellong", "failing"]' sudo -EHu temboard temboard-agent`. `
