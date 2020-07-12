.. _structure:

Structure
=========

Project consists of a standard structure which includes:

.rkd
~~~~

RiotKit-Do directory, where you can define custom tasks, there are also temporary files and logs stored (ADVANCED)

apps/conf/
~~~~~~~~~~

docker-compose YAML files with definitions of containers, networks and volumes

apps/conf.dev/
~~~~~~~~~~~~~~

Same as apps/conf, but enabled only on development environment

apps/profile/
~~~~~~~~~~~~~

Defined service profiles that allows to select services on which you operate in given command (eg. wordpress profile = all instances of wordpress)

apps/healthchecks/
~~~~~~~~~~~~~~~~~~

RiotKit's InfraCheck integration, here are placed all of the healthcheck definitions (see section about health and monitoring)

apps/repos-enabled/
~~~~~~~~~~~~~~~~~~~

GIT repositories definitions (see section about applications from external GIT repositories)

apps/www-data/
~~~~~~~~~~~~~~

Cloned applications from GIT (see section about applications from external GIT repositories)

containers/
~~~~~~~~~~~

Configuration data mounted via bind-mount to inside containers (should be read-only and versioned by GIT)

data/
~~~~~

Bind-mounted volume storage for containers, only data that is generated dynamically by containers is stored there.

**Example use cases:**

- Database data eg. /var/lib/mysql
- Generated SSL certificates storage
- NGINX generated configurations

hooks.d/
~~~~~~~~

Scripts that are executed at given time in the Harbor lifecycle (eg. pre-start, post-start, pre-upgrade, ...)
See section about hooks.

.. code:: bash

    hooks.d/
    hooks.d/pre-upgrade
    hooks.d/(...)
    hooks.d/post-start

Keeping standards
-----------------

*KISS - keep it simple stupid*

By keeping standards in your project you make sure, that any person that joins your project or a contributor could be satisfied
with Harbor documentation. Any outstanding solutions would require you to create extra documentation in your project.


OK, got it, let's learn :ref:`basic commands`
---------------------------------------------
