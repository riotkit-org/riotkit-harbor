.. _features:

Features
========

Service discovery with SSL
--------------------------

Whenever you run a new application, even without restarting the whole environment, the **gateway_proxy_gen** container
is being notified about it and creates an nginx cnofiguration to expose your application. **gateway_letsencrypt** is also
notified and generates a SSL configuration, right after nginx is ready.

Step-by-step schema:

1. **gateway_proxy_gen** listens to docker events
2. **gateway_proxy_gen** generates nginx.conf for each TAGGED service in docker network (VIRTUAL_HOST, VIRTUAL_PORT, LETSENCRYPT_HOST and LETSENCRYPT_EMAIL must be present)
3. **gateway_letsencrypt** generates SSL certificates for recently added domains
4. **gateway** is being reloaded and uses new nginx.conf with SSL certificates

FAQ:

1. Multiple domains: Separate them by comma
2. For advanced usages see: docker-gen_ documentation
3. I need to modify nginx.conf, how to? It's easy. There are two solutions:

   a) Create a file with domain name in the **./containers/nginx/vhost.d** directory

    Example "test.mydomain.org" file:

    .. code:: yaml

        ## Start of configuration add by letsencrypt container
        location ^~ /.well-known/acme-challenge/ {
            auth_basic off;
            allow all;
            root /usr/share/nginx/html;
            try_files $uri =404;
            break;
        }
        ## End of configuration add by letsencrypt container

        proxy_read_timeout 120s;


    b) Modify directly the template from which the nginx.conf is created


*NOTE: During the make start the docker-gen container is modifying files in vhost.d directory. On production a script reset-nginx-conf-permissions.sh in make stop will attempt to restore file contents to allow git pull execution later*

.. _docker-gen: https://github.com/jwilder/docker-gen

Services dashboard
------------------

Often non-technical people are not aware of what services are actually hosted. There we resolve this problem
with an automatically generated list of running web-apps.

Applications needs to be tagged with docker labels, example:

.. code:: yaml

    org.riotkit.dashboard.enabled: true
    org.riotkit.dashboard.description: 'Dashboard - a list of all hosted websites running on this network'
    org.riotkit.dashboard.icon: 'pe-7s-browser'
    org.riotkit.dashboard.only_for_admin: false

.. image:: _static/services-dashboard.png

Sending e-mails
---------------

Send e-mails directly or through a middle server, just by sending them on "smtp_server:25" without any authorization.
You can use any external SMTP, your own, a gmail account, or other.

.. code:: yaml

    SMARTHOST_ADDRESS=your-server.org    # your SMTP relay server address
    SMARTHOST_PORT=587
    SMARTHOST_USER=login@your-server.org
    SMARTHOST_PASSWORD=
    SMARTHOST_ALIASES=*    # forward all e-mails, you can put here eg. allowed recipient domains

If you make values empty, then the service will send mails directly.

Docker administration panel
---------------------------

We suggest to optionally use *Portainer* in case a need for web access to the environment.
*Portainer* is very lightweight and has support for almost all important features.

.. image:: _static/portainer.png

Uptime Board
------------

Dashboard with health check status. The status is fetched from an external service provider.

**Configuration in .env file:**

.. code:: yaml

    MONITORING_PROVIDERS=UptimeRobot://some-token;UptimeRobot://some-other-token

.. image:: _static/uptime-board.png

Integration with Ansible
------------------------

See: :ref:`ansible`

Templating
----------

Imagine that everything is in environment variables in **.env**, but you need to eg. initialize the MySQL database by creating multiple users and databases.
To allow keeping passwords safe in the **.env-prod**, but still automating eg. the user and password creation in databases we can use a templating mechanism.

.. code:: yaml

   Templating is GENERATING configuration files from templates, while having access to .env variables.

Workflow:

1. Create a template that will be rendered on **make start**
2. Mount compiled template to a volume eg. to the entrypoint.d directory

*Example ./containers/templates/source/mysql/access.sql.j2*

.. code:: sql

    /* transprzyjazn.pl */
    CREATE DATABASE IF NOT EXISTS transprzyjazn;
    CREATE USER IF NOT EXISTS 'transprzyjazn'@'%' IDENTIFIED BY '{{ DB_PASSWD_TRANSPRZYJAZN }}';
    GRANT ALL ON `transprzyjazn`.* TO 'transprzyjazn'@'%' IDENTIFIED BY '{{ DB_PASSWD_TRANSPRZYJAZN }}';

    /* lokatorzy.info.pl */
    CREATE DATABASE IF NOT EXISTS lokatorzy;
    CREATE USER IF NOT EXISTS 'lokatorzy'@'%' IDENTIFIED BY '{{ DB_PASSWD_LOKATORZY_INFO_PL }}';
    GRANT ALL ON `lokatorzy`.* TO 'lokatorzy'@'%' IDENTIFIED BY '{{ DB_PASSWD_LOKATORZY_INFO_PL }}';

You need to define environment variables in the **.env** (on following example: DB_PASSWD_TRANSPRZYJAZN and DB_PASSWD_LOKATORZY_INFO_PL).
The file will be rendered into **./containers/templates/compiled/mysql/access.sql.j2**
So, now you can mount the compiled mysql files directory into the MySQL container for example.

.. literalinclude:: ../../apps/conf/templates/infrastructure.db.yml.example
   :language: yaml

Backups
-------

See: :ref:`backups_guide`

Automatic containers update
---------------------------

Watchtower_ keeps an eye on containers marked with *com.centurylinklabs.watchtower.enable* label.
Each container's image is checked for update availability, if an update is available then it's pulled from registry
and the container is re-created on a new version of image.

Downtime is minimized by pulling newer versions of images at first, then re-creating containers in proper order.
Linked containers dependency chain is respected, so the containers are re-created in proper order.

To enable Watchtower, just use a template "infrastructure.updates.yml.example", copy it to the conf directory with removing ".example" suffix.

**Configuration**

By default there are a few example variables extracted into the environment. You may adjust it to your needs, turn off notifications,
or switch notifications from slack/mattermost to e-mail.

Check Watchtower_ documentation for detail.

.. code:: bash

    # watchtower
    WATCHTOWER_INTERVAL=1800
    WATCHTOWER_SLACK_HOOK=...
    WATCHTOWER_IDENTIFIER="Watchtower"

.. _Watchtower: https://github.com/v2tec/watchtower

Maintenance mode
----------------

When there are technical issues you may possibly want to show a nice error page, instead of "could not connect to redis".
To achieve this goal RiotKit's environment implements a **maintenance mode**.

**How it works**

- The gateway is checking if */maintenance/on* file exists, if yes, then displays a maintenance page for all domains/containers labelled with "org.riotkit.useMaintenanceMode: true"
- You can turn on/off manually maintenance mode with "make maintenance_on" and "make maintenance_off"
- You can turn it on/off AUTOMATICALLY using infracheck healthchecks, add file creation and deletion as hooks (infracheck executes all checks every one minute by default)


**Docker label required to enable maintenance mode for selected container**

.. code:: yaml

    org.riotkit.useMaintenanceMode: true

**Toggle from shell**

.. code:: bash

    make maintenance_on
    make maintenance_off

**Automatic maintenance mode with Infracheck**

Infracheck can execute checks each 1 minute (it is configurable via CHECK_INTERVAL), triggering hooks on success and failure.
This means that we can turn on the maintenance mode, when for example MySQL will go down for a backup process.

.. code:: json

    {
        "type": "port-open",
        "input": {
            "po_port": "3306",
            "po_host": "db_mysql",
            "po_timeout": "1"
        },
        "hooks": {
            "on_each_down": [
                "touch /maintenance/on"
            ],
            "on_each_up": [
                "rm -f /maintenance/on"
            ]
        }
    }

**Modifying HTML templates**

Everything is placed at *./containers/nginx/maintenance* and mounted as volume.

WWW to non-www redirection
--------------------------

To enable automatic redirection from www. to non-www domain you need to use a label and inform also letsencrypt about a subdomain.

.. code:: yaml

    environment:
        - VIRTUAL_HOST=aitrus.info${DOMAIN_SUFFIX}
        - LETSENCRYPT_HOST=aitrus.info${DOMAIN_SUFFIX},www.aitrus.info${DOMAIN_SUFFIX}
    labels:
        org.riotkit.redirectFromWWW: true
