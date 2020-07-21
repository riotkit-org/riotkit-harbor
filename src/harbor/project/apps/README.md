Applications
============

```bash
# docker-compose configurations, managed by Makefile (turning on/off)
./conf

# thin-deployer configuration for automatic deploy via webhook
./continuous-deployment 

# health checks for applications, will allow to monitor the status of the server and services
# including eg. 'is there enough disk space', 'is the mysql listening at port 3306' etc.
./healthchecks

# git repositories for applications that are mounted as volume to their images
# This pattern allows to clone applications via GIT and mount via volume to some eg. PHP7 + Apache/Nginx container
./www-data

# configuration of git repositories for applications that are stored in the ./www-data
./repos-enabled
```
