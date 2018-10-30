# Upgrade `1.1` to `1.2` (RHEL/CentOS)

Stop `temboard` service:
```shell
sudo systemctl stop temboard
```

New package installation:
```shell
sudo yum install temboard
```

Start `temboard` service:
```shell
sudo systemctl start temboard
```
