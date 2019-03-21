
Docker Project Template
=======================

Comprehensive single-server docker deployment template. Perfect for smaller and medium projects.
Unified production and development environment, with minimum amount of differences.

.. image:: _static/env-differences.png
    :align: center

**Includes:**

- Service discovery, automatic SSL
- Support for webhooks
- Ansible integration (ready to use role)
- Encrypted production credentials (.env-prod)
- Modularity, template is split into parts that could be enabled/disabled
- YAML based configuration, clear and easy to maintain
- Health checks integration + simple dashboard
- Services index (to publish list of installed apps for non-technical users)
- Automatic backups to external server (File Repository integration)
- Ready-to-use SMTP relay, easy to configure
- Support for git-based projects mounted as volumes
- Updater to keep your template up-to-date with docker-project-template

**Goals:**

- Provide complete, automated infrastructure
- Easy of use and easy to understand

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   first-steps
   structure
   general_concept
   configuration_conception
   features
   ansible
   configuration_reference
   guides/cookbook


From authors
============

Project was started as a part of RiotKit initiative, for the needs of grassroot organizations such as:

- Fighting for better working conditions syndicalist (International Workers Association for example)
- Tenants rights organizations
- Various grassroot organizations that are helping people to organize themselves without authority

.. rst-class:: language-en align-center

*RiotKit Collective*
