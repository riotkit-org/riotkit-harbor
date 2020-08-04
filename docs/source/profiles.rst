Profiles - matching services by query
=====================================

Harbor 2.0 introduced Service Profiles to make operating only on selected services possible.
The profiles are selectors that picks services you want to operate on.

**Benefits**

- Secure. Services that should not be touched are not touched
- Handy. Can be used in :code:`harbor :deployment:apply` task when deploying to production environment to update only part of services (eg. all instances of data collecting application)
- Flexible. The syntax of the filter is pure Python, you can create as much advanced queries as far as you would be able to understand them :)

Example
-------

Given we have a "gateway" selector, that picks all services that name begins with "gateway\_"

**apps/profile/gateway.profile.py**

.. code:: python

    name.startswith('gateway\_')


Now we can use it in all service management and environment stop/start tasks, for example :code:`harbor :start --profile=gateway`

Syntax
------

+----------+------------------------------------------------------+
| Variable | Description                                          |
+----------+------------------------------------------------------+
| name     | Name of the service (string)                         |
+----------+------------------------------------------------------+
| service  | Service attributes, docker-compose definition (dict) |
+----------+------------------------------------------------------+


**Notes:**

- Always check every node in dictionary for existence - Example: 1) labels, 2) labels.some-label

**Advanced example:**

.. code:: python

     "labels" in service and "org.riotkit.group" in service['labels'] and service['labels']['org.riotkit.group'] == "database"
