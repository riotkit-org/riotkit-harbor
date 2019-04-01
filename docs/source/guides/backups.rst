.. _backups_guide:

Guide to failure-safe server
============================

The environment template natively chooses RiotKit's File Repository as the backups automation.
Requirement: You need to have a server running File Repository, check file-repository_.

Example *infrastructure.backup.yaml*

.. literalinclude:: ../../apps/conf/templates/infrastructure.backup.yml.example
   :language: yaml

**Configuration**

1. In **./containers/backup/bahub.conf.yaml** define backup definitions, a recovery plan, passwords. Take a look at the File Repository's documentation there: file-repository.docs.riotkit.org_
2. All collection ids, passwords extract to **.env** file, example: **collection_id: "${BACKUPS_PORTAINER_COLLECTION_ID}"**
3. Schedule some backup jobs in **./containers/backup/cron** eg. **0 1 * * MON bahub backup db**

.. code:: bash

    BACKUPS_URL=https://api.backups.your-project.org
    BACKUPS_TOKEN=your-file-repository-token
    BACKUPS_PASSPHRASE=with-this-encryption-key-backups-will-be-encrypted
    # possible values: aes-128-cbc, aes-256-cbc, see Bahub documentation
    BACKUPS_ENCRYPTION_METHOD=aes-128-cbc
    # container name from the YAML file
    BACKUPS_CONTAINER=backup

**Recovery from backup**

There are multiple cases when you need to recover multiple containers, or all containers from latest version from backup.

Example cases:

- Server failure, need to recreate the server
- Server was compromised "hacked", need to restore latest copy of data
- Migrating from development environment into production-ready, working live server
- Migrating from server to server

.. code:: bash

    # will restore all services defined in bahub.conf.yaml into latest copy from backup server
    make recover_from_backup

    ./bin/backup

*Note: Ansible deployment could attempt to take latest versions from backup when doing a first deploy on a server*

.. _file-repository: https://github.com/riotkit-org/file-repository
.. _file-repository.docs.riotkit.org: https://file-repository.docs.riotkit.org/en/latest/client/configuration-reference.html
