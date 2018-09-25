Docker Project Template
=======================

docker-compose based template which features a complete infrastructure for any project.

Includes:
- Project-based management, one configuration per project, `make config_enable APP_NAME=some-app, # ...`
- GIT based projects management (`make update APP_NAME=some-app` will update app from git if its configured as a volume)
- Infrastructural health checks
- SMTP server
- Docker administration panel (allows to quickly log-in and eg. restart some service or repair via web-shell)
- Webhook handler for automatic deployment (push to git to deploy an update on target server)
