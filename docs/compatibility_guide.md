# Compatibility Guide

Temboard is designed to interact with many components: systemd, PostgreSQL,
agents, etc.

As we are trying to find the right balance between innovation and backward
compatibility, we define a comprehensive list of platforms and software that
we support for each version.

## Temboard 9 UNREALEASED

|                |                                            |
| -------------- | -------------------------------------------|
| Linux          | Debian 11 up to 12, RHEL 8 and 9            |
| Python         | 3.6+                                       |
| Postgres       | 12 to 17                                   |
| Temboard Agent | 8.2 and later

## Temboard 8

Temboard 8 was released in May 2022.

Each minor release (e.g. `8.1`, `8.2`, etc.) is compatible with the following
components:

|                |                                            |
| -------------- | -------------------------------------------|
| Linux          | Debian 9 up to 11, RHEL 7 and 8            |
| Python         | 3.6+                                       |
| Postgres       | 10 to 14                                   |
| Temboard Agent | 7.11 and 8.2                               |

## Temboard 7

Temboard 7 was released in October 2020 and supported until May 2022.
It is now EOL.

|                |                                            |
| -------------- | -------------------------------------------|
| Linux          | Debian 9 up to 11, RHEL 7 and 8            |
| Python         | 2.7 and 3.5+
| Postgres       | 9.6 up to 13                               |
| Temboard Agent | 6.2 and 7.11                               |
