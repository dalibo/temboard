QUICK START
================================================================================

If you want to have a quick look at Temboard, here's 3 steps to deploy a testing
environement composed of 3 PostgreSQL instances ( 9.4, 9.5 and 9.6 ) and central
Temboard server.  

1- Install docker and Install docker-compose

2- Fetch our pre-configured compose file and launch it

```
wget
https://raw.githubusercontent.com/dalibo/docker/master/temboard/docker-compose.yml
docker-compose up
```

3- Go to <https://127.0.0.1:8888>

* The temboard web server is listening to the local LAN. 
* Connect to the Temboard server with `admin / admin`
* Connect to each Postgres instance with `alice / alice`


Warnings
-------------------------------------------------------------------------------

**DO NOT USE THIS IN PRODUCTION**.                                                           
                                                                   
Obviously these docker machines are designed for testing and demo. All database
access are set to ``trust``, the SSL certificate is self-signed and the default
passwords are public.

If you want to deploy Temboard in a production environment, take some time to
read the [INSTALL](docs/INSTALL.md) documentation or go to
<http://temboard.readthedocs.io> 



Tips
------------------------------------------------------------------------------- 

- If you're already running a PostgreSQL instance on your machine, you might
  encounter conflicts with ports 5433, 5434 and 5435. If so, you can modify the
  `docker-compose.yml` file and choose alternative ports

- If you run docker on a distant linux server: build a simple SSH tunnel to 
  reach to temboard server without exposing it on the internet :

        ```
			  ssh -L 8888:localhost:8888 your_server_ip
        ```
