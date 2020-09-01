.. _creating practical services with volumes, subdomains, credentials and more:

Creating practical services with volumes, subdomains, passing credentials
=========================================================================

Harbor is a complete framework for building flexible multi-container environments, to complete it's mission
Harbor provides set of tools and patterns described in this documentation chapter.

Connecting domains, subdomains and optionally SSL
-------------------------------------------------

Domains and subdomains are automatically discovered by :ref:`JWilder's Docker-Gen <https://github.com/jwilder/docker-gen>`, when a container is started.

Docker-gen container, later called **"service discovery"** collects environment variables - including **VIRTUAL_HOST** and **VIRTUAL_PORT**
for each running container, then generates NGINX configuration file and calls reload.

Similar mechanism is practiced by :ref:`docker-letsencrypt-nginx-proxy-companion <https://github.com/nginx-proxy/docker-letsencrypt-nginx-proxy-companion>` to automatically
connect Let's Encrypt certificate - **LETSENCRYPT_HOST** and **LETSENCRYPT_EMAIL** environment variables are required to do so.


**Example:**

.. code:: yaml

    version: 2.4
    services:
        app_web_mattermost:
        image: mattermost/mattermost-prod-web:5.23.2
        depends_on:
            - app_mattermost
        environment:
            APP_HOST: "app_mattermost"
            APP_PORT: "8000"

            # gateway configuration
            VIRTUAL_HOST: "mattermost.${MAIN_DOMAIN}${DOMAIN_SUFFIX}"
            VIRTUAL_PORT: "80"
            LETSENCRYPT_HOST: "mattermost.${MAIN_DOMAIN}${DOMAIN_SUFFIX}"
            LETSENCRYPT_EMAIL: "${LETSENCRYPT_EMAIL}"


.. code:: bash

    MAIN_DOMAIN=riotkit.org
    DOMAIN_SUFFIX=.localhost
    LETSENCRYPT_EMAIL=noreply@riotkit.org


**MAIN_DOMAIN, DOMAIN_SUFFIX and LETSENCRYPT_EMAIL convention**

- Use MAIN_DOMAIN to specify a main domain if hosting services under multiple subdomains
- DOMAIN_SUFFIX, on development environment set to ".localhost" - in result on Linux you will be able to access services like on production but under localhost sudomain eg. my-subdomain.riotkit.org.localhost. Please note: When using :code:`harbor :deployment:apply` the DOMAIN_SUFFIX is automatically erased when deploying to production server
- LETSENCRYPT_EMAIL allows to have a globally defined e-mail address for all services


Passing credentials and configuration options
---------------------------------------------

Most universal way to configure services is to pass environment variables.
Passwords, sensitive data and common values shared between services put in :code:`.env` file, then encrypt it using Ansible Vault command :code:`harbor :env:encrypt`.
In result a :code:`.env-prod` file will be produced. Don't commit :code:`.env` to git - add it to ignore, commit :code:`.env-prod` instead.

When deploying to production server with :code:`harbor :deployment:apply` mechanism the :code:`.env-prod` will be decrypted on-the-fly and placed as :code:`.env` on the destination server.

.. code:: yaml

    version: 2.4
    services:
        postgres:
            image: postgres:12.4
            environment:
                POSTGRES_USER: "postgres"
                POSTGRES_PASSWORD: "${DB_PASSWD}"
                POSTGRES_DATABASE: "mydb"
            expose:
                - 5432
            volumes:
                - ./data/pg:/var/lib/pgsql

.. code:: bash

    DB_PASSWD=my-passwd


**Note:** :code:`.env` is read by docker-compose and by RKD in makefile.yaml by default. It is a good place to put your configuration options

Volumes
-------

In previous chapter we were talking about naming conventions, remember? There is a distinction for static and dynamic volumes.

- Static volumes are kept in GIT repository, those are usually versioned configuration files
- Dynamic volumes are application data (database binary files, user file uploads)

.. code:: yaml

    version: 2.4
    services:
        my-website:
            image: nginx:1.19
            environment:
                VIRTUAL_HOST: "my-website.localhost"
                VIRTUAL_PORT: "80"
            volumes:
                # in www-data we keep other cloned git repositories managed by Harbor
                - ./apps/www-data/my-website:/var/www/html
                - ./container/my-website/nginx.conf:/etc/nginx/nginx.conf:ro

        postgres:
            image: postgres:12.4
            environment:
                POSTGRES_USER: "postgres"
                POSTGRES_PASSWORD: "${DB_PASSWD}"
                POSTGRES_DATABASE: "mydb"
            expose:
                - 5432
            volumes:
                - ./data/pg:/var/lib/pgsql
