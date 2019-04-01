Guide to a perfect Wordpress page deployment
============================================

.. image:: ../_static/wp-logo.png
    :align: center

Following guide will give you following advantages:

- Automatic updates of Wordpress CMS
- Automatic SSL
- Automatic backup of the files
- Site theme managed by GIT, versioned
- Automatic creation of the configuration, database
- Do not need to copy anything manually to production, deploys first working version from prepared backups

1. Database
-----------

You need a database that will create your user with proper password, create internally a database.

.. literalinclude:: ../../../apps/conf/templates/infrastructure.db.yml.example
   :language: yaml

2. Backups configuration (optional)
-----------------------------------

See: Backups section of :ref:`features`

*Notice: It's optional. But you will need to copy your post images (uploads) to production manually, and later do manual backups of it. Consider having a $3 dollar/month 100GB VPS that stores backups of your files.*

3. Adding theme to GIT
----------------------

Create a git repository on the git hosting, eg. on bitbucket, github.
Go into the eg. wp-content/themes/THEME-NAME, and make a git repository from it.

.. code:: bash

    cd wp-content/themes/THEME-NAME
    git init
    git add .
    git commit -m "Added to git"
    git remote add origin REPOSITORY-URL-HERE
    git push origin master

Now your Wordpress theme is in a git repository! You can use it, to version it, deploy updates to the server!

4. Connect theme git repository to environment
----------------------------------------------

To automatically do a git pull on deployment of the environment, we can make the repository to be managed by environment.

In **./apps/repos-enabled/SOME-APP-NAME.sh** put a simple configuration script:

.. code:: bash

    #!/bin/bash
    # replace this with project name on github, bitbucket, gogs or other
    export GIT_PROJECT_NAME=app.transprzyjazn

    # the directory in ./apps/www-data/ to mount later in the YAML file to the container
    export GIT_PROJECT_DIR=app.transprzyjazn
    export WRITABLE_DIRS=""

Now you can fetch a new version with:

.. code:: bash

    make update APP_NAME=SOME-APP-NAME

Or you can update all your themes for all websites:

.. code:: bash

    make update_all


5. Make sure the environment is configured to work with GIT
-----------------------------------------------------------

In the **.env** file there is a section to configure link to a GIT server.

.. code:: bash

    # git deployment specification for applications
    GIT_SERVER=github.com
    GIT_PROTO=https
    GIT_USER=my-deploy-user
    GIT_PASSWORD=
    GIT_ORG_NAME=my-org-at-git-server

This will make all connected repositories in **./apps/repos-enabled/** to use this global GIT server by default.
But each repository can override those settings in the shell configuration file.

6. Create YAML files and update .env file
-----------------------------------------

When your website theme is in GIT, and is managed by environment you need to pass it as a volume to the Wordpress container.
The path to the theme files would be **./apps/www-data/{{ PUT GIT_PROJECT_DIR VALUE HERE, IT CANNOT BE A VARIABLE }}**

*Protip: Extract database password into .env for security reasons*

*Protip: Use MAIN_DOMAIN and DOMAIN_SUFFIX convention to have benefits of it*

.. code:: yaml

    version: "2"
    services:
        app_transprzyjazn:
            image: wolnosciowiec/wp-auto-update
            expose: ['80']
            volumes:
                - ./data/wordpress/app.transprzyjazn:/var/www/html
                - ./apps/www-data/app.transprzyjazn:/var/www/html/wp-content/themes/freddo
            environment:
                - WORDPRESS_DB_HOST=db
                - WORDPRESS_DB_USER=transprzyjazn
                - WORDPRESS_DB_PASSWORD=${DB_PASSWD_TRANSPRZYJAZN}
                - WORDPRESS_DB_NAME=transprzyjazn

                # gateway configuration
                - VIRTUAL_HOST=transprzyjazn.pl${DOMAIN_SUFFIX}
                - VIRTUAL_PORT=80
                - LETSENCRYPT_HOST=transprzyjazn.pl${DOMAIN_SUFFIX}
                - LETSENCRYPT_EMAIL=${LETSENCRYPT_EMAIL}

7. Have fun!
------------
