Templates
=========

Files in this directory will be rendered into project root directory, preserving the directories structure.

Example
-------

`templates/containers/nginx/nginx.conf.j2` -> `containers/nginx/nginx.conf`

Use case
--------

- Prepare configuration files and scripts on-the-fly
- Inject passwords from .env (so the files will not keep unencrypted secrets in the repository)
