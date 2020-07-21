.. _basic commands:

Basic commands
==============

Harbor defines a lot of RKD tasks, that automates preparing changes to project as well as operating on live organism.

At first we would like you to get familiar with our Snippet Cooperative, which is a place to share a code with others - for you now it means you can install an application with a single command.


Installing applications from Snippet Cooperative
------------------------------------------------

Browse the catalogue of applications at: https://github.com/riotkit-org/harbor-snippet-cooperative
Then, perform an installation within a single command.

.. code:: bash

    # at first do a repository sync, later you don't need to do it all the time
    harbor :cooperative:sync :cooperative:install harbor/redis

Starting, upgrading and stopping services
-----------------------------------------

Basic tasks lets you control the services running in your environment, just like you were doing before with **docker ps**
but with a difference that Harbor interface is more domain-focused interface.

.. code:: bash

    # create and start containers
    harbor :start

    # pull new images, update git repositories, then start
    harbor :upgrade

    # start selected service
    harbor :service:up hello

    # remove selected service
    harbor :service:rm hello

    # list all services, running and not running
    harbor :service:list

    # check a report of running service
    harbor :service:report hello

Controlling maintenance mode on production
------------------------------------------

Sometimes, when bad things happens, or a scheduled repair is planned a maintenance mode is required.
Harbor provides a simple maintenance mode in 3 ways: global, per-service, per-domain

.. code:: bash

    # maintenance mode per single service
    harbor :maintenance:on --service hello

    # per single domain
    harbor :maintenance:on --domain domain-name.org

    # global maintenance mode - for all services
    harbor :maintenance:on --global

Diagnosing issues (advanced usage on production)
------------------------------------------------

    # do the docker-compose ps, in case you need
    harbor :diagnostic:compose:ps

    # in case you need a full docker-compose arguments used by Harbor to execute some commands manually
    harbor :diagnostic:dump-compose-args

    # dump all yamls to big one for analysis
    harbor :diagnostic:compose:config

    # force regenerate all Letsencrypt certificates (use with caution, there are limits of hits on Letsencrypt)
    harbor :gateway:ssl:regenerate

    # reload gateway in case, when the the nginx.tmpl was modified
    harbor :gateway:reload
