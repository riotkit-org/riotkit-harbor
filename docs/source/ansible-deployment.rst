Deploying to production with Ansible
====================================

Concept - Single key to all credentials
---------------------------------------

Harbor 2.0 standardizes the way of deploying itself to production servers,
introducing a simplified deployment from single repository with one passphrase for all secrets.

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
