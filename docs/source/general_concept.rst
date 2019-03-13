General conception
==================

The idea of this environment template is to provide a base for small and medium projects, deployed on a single server.
With a high focus on ease of use.

There are a few **design patterns**, that are the basis of the environment conception.

Management from Makefile
------------------------

Everything important goes into the Makefile. There are no plain bash scripts outside of the Makefile.
The project is built in purely Makefile + YAML + docs + misc files.

.. code:: yaml

    make start
    make check_status
    make list_all_hosts
    make stop
    make build_docs
    make encrypt_env_prod

    # ...
    # and others

Multiple compose files can be toggled on/off
--------------------------------------------

Service definitions in Docker Compose format are kept in **./apps/conf** directory.
Services that are temporarily disabled are marked with ".disabled" at the end of filename.


.. code:: yaml

    ✗ make list_configs
    dashboard
    deployer
    health
    service-discovery
    smtp
    ssl
    technical
    uptimeboard

    ✗ make config_disable APP_NAME=ssl
     >> Use APP_NAME eg. make config_disable APP_NAME=iwa-ait
     OK, ssl was disabled.
    ✗ make config_enable APP_NAME=ssl
     >> Use APP_NAME eg. make config_disable APP_NAME=iwa-ait
     OK, ssl is now enabled.

Configuration in one file that could be encrypted
-------------------------------------------------

Good practice is to extract environment variables into .env files, instead of hard-coding values into services YAML definitions.
That makes a **.env** file from which we can use environment variables in YAML files with syntax eg. ${VAR_NAME}

As the **.env** cannot be pushed into the repository, there is a possibility to push **.env-prod** as a encrypted file with ansible-vault.

.. code:: yaml

    make encrypt_env_prod


Main domain and domain suffix concept
-------------------------------------

**MAIN_DOMAIN** can be defined in **.env** and reused in YAML files togeter with **DOMAIN_SUFFIX**.
It opens huge possibility of creating test environments which have different DNS settings.
Sounds like a theory? Let's see a practical example!

**Scenario for test environment:**

.. code:: cucumber

    Given It's a TEST environment
    So the variables are configured in following way
    | DOMAIN_SUFFIX | .localhost  |
    | MAIN_DOMAIN   | iwa-ait.org |
    When application has set VIRTUAL_HOST=some-service.${MAIN_DOMAIN}${DOMAIN_SUFFIX}
    Then the SOME SERVICE will have address http://some-service.iwa-ait.org.localhost

**Scenario for production environment:**

.. code:: cucumber

    Given It's a TEST environment
    So the variables are configured in following way
    | DOMAIN_SUFFIX |             |
    | MAIN_DOMAIN   | iwa-ait.org |
    When application has set VIRTUAL_HOST=some-service.${MAIN_DOMAIN}${DOMAIN_SUFFIX}
    Then the SOME SERVICE will have address http://some-service.iwa-ait.org


It's so much flexible that you can host multiple subdomains on main domain, but you can also use totally different domain.

**Example:**

.. code:: bash

    MAIN_DOMAIN=iwa-ait.org
    DOMAIN_SUFFIX=.localhost

.. code:: yaml

    first:
        environment:
            - VIRTUAL_HOST=some-service.${MAIN_DOMAIN}${DOMAIN_SUFFIX}

    second:
        environment:
            - VIRTUAL_HOST=other-service.example.org${DOMAIN_SUFFIX}

**In result of above example you will have services under domains in test environment:**

- some-service.iwa-ait.org.localhost
- other-service.example.org.localhost
