Apps hosted on GIT and mounted as volumes
=========================================

Applications based on CMS such as Wordpress and Drupal are not easy to pack into a docker container, as the user
is allowed to manage them with web panel.


The solution for this situation could be to:

- Keep the constant files versioned in GIT (eg. website theme)
- Put all the files into the external backup, see :ref:`backups_guide`

1. Configuring environment globally
-----------------------------------

The general concept is to have a single organization on github, bitbucket, gogs or other git server, and multiple repositories in it.
But it is of course possible to have multiple and leave some of the global fields empty.

**Just play with those environment variables in the .env file:**

.. code:: bash

    # git deployment specification for applications
    GIT_SERVER=github.com
    GIT_PROTO=https
    GIT_USER=my-deploy-user
    GIT_PASSWORD=
    GIT_ORG_NAME=my-org-at-git-server

Remember, that all of those variables can be later overwritten by single repository configuration.

2. Making application manageable by environment
-----------------------------------------------

In *./apps/repos-enabled* create a bash script, it's actually not a script, but a configuration in shell syntax.
Variables are inherited from **.env** file, so you can overwrite them there per-repository.

**Example**

.. literalinclude:: ../../../apps/repos-enabled/some-app.sh
   :language: bash

*Good practice tip: It is good to have a read-only deployment user, to not leak your passwords with write-access*

3. Deploying
------------

Volume-based applications are deployed during *make deployment_pre*, when deploying with Ansible.
To trigger a manual deploy, please check:

.. code:: bash

    # deploy all git-volume-based applications
    make update_all

    # deploy single application
    make update APP_NAME=some-app

**What is the update command doing?**

The update command is cloning the repository IF IT DOES NOT EXIST, in other case it is doing a git pull.
