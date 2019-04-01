.. _databases_guide:

Guide to deploying databases
============================

Databases are not stateless, it's deploy is difficult than a deploy of a regular service.
In this guide we focus on MySQL, but it's really up to you what database you will use.

Goals:

- Running up-to-date database engine
- Automatically made backup
- Migration of the data on deploy
- Administration panel for overview

1. Basic configuration
----------------------

**infrastructure.db.yml.example**

.. literalinclude:: ../../../apps/conf/templates/infrastructure.db.yml.example
   :language: yaml

2. Keep the database server up-to-date (optional)
-------------------------------------------------

You may want to enable the Watchtower to update the database image automatically, to do this
please tag the database image with a label **com.centurylinklabs.watchtower.enable: true**

**infrastructure.updates.yml.example**

.. literalinclude:: ../../../apps/conf/templates/infrastructure.updates.yml.example
   :language: yaml

3. Have a backup (optional)
---------------------------

It's recommended to use File Repository as backup storage, but it's totally optional as it requires an additional server in your infrastructure.

Read more here: file-repository_

**Example bahub configuration:**

.. code::yaml

    db:
        type: docker_volumes
        container: "${COMPOSE_PROJECT_NAME}_db_1"
        access: primary
        encryption: secured
        collection_id: "${BACKUPS_DB_COLLECTION}"
        paths:
            - "/var/lib/mysql"

You need to define **BACKUPS_DB_COLLECTION** in the **.env** file.

.. _file-repository: https://github.com/riotkit-org/file-repository

4. Automate migrations (optional)
---------------------------------

Adding a new application to the network requires a manual user creation, database creation - this also can be automated optionally.

1. Create a _migrations database in the SQL
2. Enable **infrastructure.db_migrations.yml** configuration file
3. To execute SQL statements just right after deployment, put them into **./containers/migrations/prod** and enable the **db_migrations** configuration file
4. (Optionally) Use templating mechanism, put a SQL template in JINJA2 format in **./containers/templates/source**, so it will appear compiled in **/templates** inside of the container

**infrastructure.db_migrations.yml.example**

.. literalinclude:: ../../../apps/conf/templates/infrastructure.db_migrations.yml.example
   :language: yaml

**Example of automatically generated SQL files with using variables from .env file**

./containers/templates/source/access.sql.j2

.. code:: sql

    CREATE DATABASE IF NOT EXISTS zsp;
    CREATE USER IF NOT EXISTS 'some_page'@'%' IDENTIFIED BY '{{ DB_PASSWD_SOME_PAGE }}';
    GRANT ALL ON `some_page`.* TO 'some_page'@'%' IDENTIFIED BY '{{ DB_PASSWD_SOME_PAGE }}';

./containers/migrations/prod/1553701697-some-page.sql

.. code:: sql

    -- Migration: some-page
    -- Created at: 2019-03-27 16:46
    -- ====  UP  ====

    source /templates/access.sql;

    -- ==== DOWN ====


5. When database will go down, show maintenance page (optional)
---------------------------------------------------------------

Infracheck is doing health checks of the infrastructure. The "infrastructure.health.yml" needs to be enabled at first.

**Example health check**

*Please notice the on_each_down and on_each_up sections.*

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
