First steps
===========

Naturally you need **docker**, **docker-compose** on a Linux-based host OS, basic understanding of how the docker containers works and at least little Linux shell experience.

To install:

- git (repository)
- docker (get.docker.com)
- docker-compose (get.docker.com)

Let's go!
---------

Project template is hosted on **git** version control system, with git it's possible to update your environment with newer template version.
Updates are not mandatory, and the template may be not always backwards compatible, because it's a template you can use fully or only parts of it.

1. Create your project directory (replace "your-project-name" with a proper name):

.. code:: bash

    mkdir your-project-dir
    cd your-project-dir

    # initialize git repository, at least locally
    git init

    # download the project files using updater script
    curl -s https://raw.githubusercontent.com/zwiazeksyndykalistowpolski/docker-project-template/master/update-from-template.sh | bash

2. Take a look around, check documentation for:

- :ref:`structure`
- :ref:`features` 
- :ref:`configuration_reference`

You may be interested with placing your docker container definitions at **./apps/conf**

3. Configure the project:

Before you will start changing the configuration, please a look at the :ref:`configuration_conception`.

.. code:: bash

    cp .env-default .env
    edit .env

4. Start the project:

.. code:: bash

    make help
    make start

5. Access configured domain on web browser

Go to http://the-configured-domain-here.localhost, enjoy.

You may want to check a complete example: :ref:`general_concept`

