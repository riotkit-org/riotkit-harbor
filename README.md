Docker Project Template
=======================

[![Documentation Status](https://readthedocs.org/projects/riotkit-docker-template/badge/?version=latest)](https://environment.docs.riotkit.org/en/latest/?badge=latest)

docker-compose + git based template which features a complete infrastructure for any project.

Includes:
- Project-based management, one configuration per project, `make config_enable APP_NAME=some-app, # ...`
- GIT based projects management (`make update APP_NAME=some-app` will update app from git if its configured as a volume)
- Infrastructural health checks
- SMTP server
- Docker administration panel (allows to quickly log-in and eg. restart some service or repair via web-shell)
- Webhook handler for automatic deployment (push to git to deploy an update on target server)
- Automatic backups with disaster recovery
- Integration with Ansible
- Encrypted production .env file (.env-prod)

Getting started
---------------

### Creating a project from template

This architecture requires to keep your project in a git repository, so you need to create one.

```bash
mkdir your-project-dir
cd your-project-dir

# initialize git repository, at least locally
git init 

# download the project files using updater script
curl -s https://raw.githubusercontent.com/riotkit-org/riotkit-harbor/master/update-from-template.sh | bash
```

Updating existing project
-------------------------

This template contains predefined configuration and tools for managing a project based on git and docker.
Even if you have your own git repository and existing changes there is a possibility to keep general things up-to-date
with the template.

At first, add important files and directories to the `./.updateignore` file, so those files or directories will not be touched.

```bash
edit ./.updateignore
curl -s https://raw.githubusercontent.com/riotkit-org/riotkit-harbor/master/update-from-template.sh | bash
```
