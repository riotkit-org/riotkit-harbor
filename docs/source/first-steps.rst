First steps
===========

Naturally you need **docker**, **docker-compose** on a Linux-based host OS, basic understanding of how the docker containers works and at least little Linux shell experience.

To install:

- git (repository)
- docker (get.docker.com)
- docker-compose (get.docker.com)

Let's go!
---------

Project template is hosted on **git** version control system and it's updater bases on it, to easily distinct changes made by you from the incoming update.

1. Create your project directory (replace "your-project-name" with a proper name):

.. code:: bash

    git clone https://git.riotkit.org/docker-project-template your-project-name
    cd your-project-name

2. Take a look around, check documentation for:

- :ref:`structure`
- :ref:`features`
- Configuration reference

3. Configure the project:

Before you will start changing the configuration, please a look at the :ref:`configuration_conception`.

.. code:: bash

    cp .env-default .env
    edit .env

4. Start the project:

.. code:: bash

    make help
    make start

