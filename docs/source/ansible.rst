.. _ansible:

Ansible deployment
==================

To have a complete, reproducible environment which includes host SSH, shell, automatic updates, users, groups, firewall, vpn an Ansible could be used.
There exists an official ready-to-use role in separate repository_.

What is Ansible?
----------------

Imagine that you do not have to log-in into your server to change it's configuration, there are easier ways.
You define a set of YAML files with TASKS TO EXECUTE to have a given result.

**Examples tasks:**

- Create user X, group Y
- Install A, B, C packages
- Block all traffic, except port 80, 22
- **Install and configure your project that is based on Docker Project Template for example**

**From Wikipedia:**

.. code:: text

    Ansible is an open-source software provisioning, configuration management, and application deployment tool



Deploying a project using this docker environment template
----------------------------------------------------------

A role from this repository_ can be used simply, for example in this way:

.. code:: yaml

    - role: blackandred.server_docker_project
      tags: project
      vars:
          deploy_user: tech.admin
          project_dir: /project
          git_deploy_url: "https://your-git-server/backup-replica-environment.git"
          git_regular_deploy_url: "https://your-git-server/backup-replica-environment.git"
          make_executable: "sudo ./make.sh"

          test_specific_env:
              - { line: "DOMAIN_SUFFIX=.localhost", regexp: '^DOMAIN_SUFFIX', title: 'env: Add domain suffix - .localhost' }

          production_specific_env:
              - { line: "DOMAIN_SUFFIX=", regexp: '^DOMAIN_SUFFIX', title: 'env: Remove domain suffix' }


1. Add above to your playbook
2. Install role with *ansible galaxy install blackandred.server_docker_project*
3. Run *ansible-playbook your-playbook.yml -i hosts.cfg -t project*

.. _repository: https://git.riotkit.org/docker-ansible-role

Storing credentials
-------------------

You will probably have a dilemma when it will go into the point to have some passwords on the production server.
The passwords should not be stored in git repository as plain text, so *.env* and *.env-default* should not be used.

There is a solution.

1. Just put everything into *.env* file locally, by default its ignored from sending to git (.gitignore), do not commit it.
2. Create *".vault-password"* file in root directory of your project repository, make sure it's in .gitignore so it will be not placed in repository
3. Optional: You can keep *".vault-password"* in safe place, eg. on your pendrive linked symbolically to the project directory
4. Use *make encrypt_env_prod* to generate *.env-prod* that will be used by Ansible to create *.env* on production server during deployment

Limited downtime deployments
----------------------------

Docker Compose has an ability to detect which service YAML file was changed and recreate only containers for changed services.
This does not apply to files mounted via volumes.


If you made a change to one of files mounted via volumes, then you need to restart the environment, or disable limited downtime feature (can be done temporarily).

To disable the limited downtime feature for a single deployment you can use a switch:

.. code:: bash

    ansible-playbook -e avoid_whole_environment_restart=False ...
