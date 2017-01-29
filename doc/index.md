
![Temboard](temboard.png)

Temboard is a powerful mangement tool for PostgreSQL. You can use it monitor, optimize or configure multiple PostgreSQL instances.

Temboard is composed of 2 basic elements:

* An lightweight [agent](#the-agent) that you need to install on every PostgreSQL server you want to manage

* A central [server](#the-server) that will control the agents and collect metrics from them.

# Quick Start

We're providing a complete testing environment based on docker:                 
                                                                                
Please read our [QUICKSTART](QUICKSTART.md) guide for more details.

# The Agent

There's 3 different ways to install the agent:

* [On Debian](temboard-agent-install-debian.md)
* [On Red hat](temboard-agent-install-rpm.md)
* [From source](temboard-agent-install-sources.md)

Then you need to [Configure](temboard-agent-configuration.md) it.




# The Server

The server can be install following one of these methods:

* [On Debian](temboard-install-debian.md)
* [On Red hat](temboard-install-rpm.md)
* [From source](temboard-install-sources.md)

Then you want proceed to [setup the repository](temboard-repository-setup.md).

For the first steps, please read the [How to](temboard-howto.md).
