.. _configuration_conception:

Configuration concept
=====================

The configuration is placed at the **.env** file, which is passed to docker-compose configuration. Services see only a few variables, or all variables (it depends if "environment" or "env_file" section was used in service configuration).
A **.env-default** file is a template containing example, default values.

.. code:: yaml

    .env
    .env-default
    .env-prod


:ref:`ansible` is using **.env-prod** when pushing application to the server, decrypting it and replacing **.env** file on the server.


    *NOTE: .env is not to store in the git. To store production credentials please use .env-prod encrypted with ansible-vault and decrypted during Ansible deployment*

    *NOTE: .env-default should not contain passwords as it is stored in git*

Test and production environment
-------------------------------

They are mostly the same except fact, that the domains are different and, the test environment does not have real SSL enabled.

**Domain suffix design pattern**, is a pattern where we have a BASE DOMAIN eg. riotkit.org, then in test environment we add a suffix, so it is riotkit.org.localhost on our test environment.
This practice gives us out-of-the-box working DNS on local testing machine.


**Example production specific .env part:**

.. code:: bash

    DOMAIN_SUFFIX=
    MAIN_DOMAIN=riotkit.org

**Example test specific .env part:**

.. code:: bash

    DOMAIN_SUFFIX=.localhost
    MAIN_DOMAIN=riotkit.org

