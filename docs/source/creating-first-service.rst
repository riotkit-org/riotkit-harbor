.. _creating first service:

Creating first service
======================

Service definitions are docker-compose.yml files, with addition of Harbor's patterns which allows to automate
and standardize the way of environment preparation.

**Few rules:**

- YAML files are stored at :code:`./apps/conf`
- The naming: :code:`apps.MY-APP-NAME.yaml` for applications, and :code:`infrastructure.MY-TECHNICAL-APP-NAME.yaml` for technical services (health checks, backups etc.)
- Volumes with configuration files eg. nginx.conf - should be in :code:`./container/MY-APP-NAME` directory
- Volumes with external git repositories should be in :code:`./apps/www-data/MY-APP-NAME` directory
- Volumes with dynamic data such as user uploads should be in :code:`./data/MY-APP-NAME` directory

Let's create first service then!
--------------------------------

Best way to create a service is to use a generator - to avoid common mistakes.

Demo: https://asciinema.org/a/348867

.. code:: bash

    harbor :cooperative:sync
    harbor :cooperative:install harbor/webservice


The below example will sync coop repositories, then use :code:`harbor/webservice` template to generate docker-compose yaml file,
that will be placed in :code:`./apps/conf` directory.

Use :code:`:service:up` task to bring up a recently created service.

.. code:: bash

    harbor :service:list
    harbor :service:up service-name


After checking that everything works correctly the service definition + configuration files placed in :code:`./container` directory should be pushed to GIT.
