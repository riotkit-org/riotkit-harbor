Deploying to production with Ansible
====================================

Concept - Single key to all credentials
---------------------------------------

Harbor 2.0 standardizes the way of deploying itself to production servers,
introducing a simplified deployment from single repository with one passphrase for all secrets.

Deployment mechanism is installing Harbor + dependencies from requirements.txt, cloning the repository, setting permissions, adding autostart with systemd and starting the project.
Please note, that it requires **all changes to be committed to git repository** before starting :code:`harbor :deployment:apply` command.

**Encrypted deployment.yml file can contain ssh passwords, ssh private key. It's safe to store it in repository - Ansible Vault is using strong AES encryption**

.. code:: yaml

    deploy_user: my-deployment-user
    deploy_group: my-deployment-user

    # Directory, where the project will be installed
    remote_dir: /home/my-deployment-user/project

    # Target repository to clone (in most cases it should be the same repository as current one)
    # leave commented for automatic detection
    #git_url: git@github.com:your-org/your-repo.git

    # Secret url is helpful, when you cannot setup working ssh-agent. Secret url is used only at deployment time, later
    # a regular URL (without credentials) is leaved on the machine
    #git_secret_url: https://user:password@github.com/your-org/your-repo.git

    # Will make a file in /etc/sudoers.d/ to allow ssh-agent passing into sudo session
    configure_sudoers: true

    nodes:
        production:
            - host: remote-host.org
              port: 2222
              user: my-deployment-user
              sudo_password: my-sudo-password

              # select between password or key-based authentication
              password: my-password
              private_key: |
                  -----BEGIN OPENSSH PRIVATE KEY-----
                  (................................)
                  -----END OPENSSH PRIVATE KEY-----


Getting started with Harbor deployments
---------------------------------------

First time you need to download a required Ansible role and optionally generate an example deployment.yml file

.. code:: bash

    harbor :deployment:files:update :deployment:create-example


Now fill up **deployment.yml** file, then perform a test deployment.

.. code:: bash

    # tip: use --ask-vault-pass if you encrypt .env file
    # tip: you need to have all changes (except deployment.yml - you can hold with this file) committed to repository before running deployment
    harbor :deployment:apply

When deployment ran smoothly and you are sure that's pretty all, then encrypt deployment.yml

.. code:: bash

    # tip: Use same key as in .env file to make it simpler
    harbor :vault:encrypt deployment.yml


Advanced usage
--------------

Use switches and environment variables to customize playbook name, inventory name, to pass Ansible Vault password, to ask for user ssh login or ssh password.

.. code:: bash

    # ask interactively for sudo password
    harbor :deployment:apply --ask-sudo-pass

    # provide a vault password in alternative way
    VAULT_PASSWORDS="oh-thats-secret" harbor :deployment:apply

    # another way to provide vault password
    echo 'VAULT_PASSWORDS="oh-thats-secret"' > /mnt/secret-encrypted-storage/.secret-env
    source .secret-env && harbor :deployment:apply


    # run witha custom playbook (place it in .rkd/deployment/
    PLAYBOOK="my-playbook.yml"  harbor :deployment:apply

    # deploying from a custom branch instead of "master"
    harbor :deployment:apply --branch primary

    # providing a key for GIT clone used to setup project repository on target machine
    harbor :deployment:apply --git-key="~/.ssh/id_rsa"
