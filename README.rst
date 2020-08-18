RiotKit's Harbor
================

.. image:: https://readthedocs.org/projects/riotkit-docker-template/badge/?version=latest
	:alt: Documentation Status
	:target: https://environment.docs.riotkit.org/en/latest/

.. image:: http://www.repostatus.org/badges/latest/active.svg
	:alt: Project Status: Active – The project has reached a stable, usable state and is being actively developed.
	:target: http://www.repostatus.org/#active

.. image:: https://img.shields.io/github/v/release/riotkit-org/riotkit-harbor?include_prereleases
	:target: https://img.shields.io/github/v/release/riotkit-org/riotkit-harbor?include_prereleases
	:alt: Github Release

.. image:: https://img.shields.io/badge/Made%20with-Python-1f425f.svg
	:target: https://img.shields.io/badge/Made%20with-Python-1f425f.svg
	:alt: Made with Python

.. image:: https://img.shields.io/pypi/l/rkd-harbor.svg
	:target: https://img.shields.io/pypi/l/rkd-harbor.svg
	:alt: License

.. image:: https://travis-ci.com/riotkit-org/riotkit-harbor.svg?branch=master
	:target: https://travis-ci.com/riotkit-org/riotkit-harbor
	:alt: Travis CI

.. image:: https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square
	:target: https://img.shields.io/badge/PRs-welcome-brightgreen.svg?style=flat-square
	:alt: PRs welcome

.. image:: https://img.shields.io/github/issues-pr/riotkit-org/riotkit-harbor.svg
	:target: https://img.shields.io/github/issues-pr/riotkit-org/riotkit-harbor.svg
	:alt: PRs open

.. image:: https://img.shields.io/github/issues/riotkit-org/riotkit-harbor.svg
	:target: https://img.shields.io/github/issues/riotkit-org/riotkit-harbor.svg
	:alt: Issues open

:code:`docker-compose` based framework for building production-like environments - developing and testing on your local computer, deploying to your server or cluster from shell or from CI.

.. image:: ./docs/demo.gif

Demo: https://asciinema.org/a/348698

Harbor
^^^^^^

Is Kubernetes or OKD too big overhead or not suitable for your environment?
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Is standard docker-compose too primitive to use in production?
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Harbor fits perfectly, while providing some of Kubernetes-like solutions in docker-compose!
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""



**Features:**

- Service discovery (pins containers into WWW domains by labelling)
- Deployment strategies: compose's standard, recreation, and **rolling-updates (zero-downtime updates)**
- Automatic Letsencrypt SSL
- Standardized directory structures and design patterns
- Ready to use snippets of code and solutions (one command to install database, Wordpress or other application from our repository)
- Ansible integration to prepare your production/testing server and deploy updates in extremely intuitive way


**Roadmap:**

**Harbor 2.1**

- Init containers support (basing on Kubernetes idea) (`#5 <https://github.com/riotkit-org/riotkit-harbor/issues/5>`_)
- delayed-request update strategy (minimum-downtime deployment with holding all HTTP requests waiting for new application) (`#11 <https://github.com/riotkit-org/riotkit-harbor/issues/11>`_)
- Webhook handling update daemon to trigger container and git updates (`#10 <https://github.com/riotkit-org/riotkit-harbor/issues/10>`_)

Read documentation for more: https://environment.docs.riotkit.org/en/latest/?badge=latest
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Changelog
---------

Harbor 2.0
""""""""""

- Service upgrade strategies: Compose-native, recreation, rolling-updates
- Rewrite from Makefile to Python
- Containers startup priority
- Maintenance mode is now not only global, but also per domain
- Development mode now supports not only .localhost domains, but also \*.xip.io

From authors
------------

We are grassroot activists for social change, so we created this software while we were helping those fantastic initiatives:

- RiotKit (https://riotkit.org)
- International Workers Association (https://iwa-ait.org)
- Anarchistyczne FAQ (http://anarchizm.info) a translation of Anarchist FAQ (https://theanarchistlibrary.org/library/the-anarchist-faq-editorial-collective-an-anarchist-faq)
- Federacja Anarchistyczna (http://federacja-anarchistyczna.pl)
- Związek Syndykalistów Polski (https://zsp.net.pl) (Polish section of IWA-AIT)
- Komitet Obrony Praw Lokatorów (https://lokatorzy.info.pl)
- Solidarity Federation (https://solfed.org.uk)
- Priama Akcia (https://priamaakcia.sk)

Special thanks to `Working Class History <https://twitter.com/wrkclasshistory>`_ for very powerful samples that we could use in our unit tests.
