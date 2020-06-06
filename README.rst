RiotKit's Harbor
================

[![Documentation Status](https://readthedocs.org/projects/riotkit-docker-template/badge/?version=latest)](https://environment.docs.riotkit.org/en/latest/?badge=latest)

`docker-compose` based framework for building production-like environments - starting on your local computer, deploying to your server or cluster.

Harbor
^^^^^^

Is Kubernetes or OKD too big overhead or not suitable for your environment?
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Is standard docker-compose too primitive to use in production?
""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

Harbor would fit perfectly, while providing some of Kubernetes-like solutions in docker-compose
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""


**Features:**

- Service discovery (pins containers into WWW domains by labelling)
- Deployment strategies: compose's standard, recreation, and **rolling-updates (zero-downtime updates)**
- Automatic Letsencrypt SSL
- Standardized directory structures and design patterns
- Ready to use snippets of code and solutions

Read documentation for more: https://environment.docs.riotkit.org/en/latest/?badge=latest
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

From authors
------------

We are grassroot activists for social change, so we created Harbor especially in mind for those fantastic initiatives:

- RiotKit (https://riotkit.org)
- International Workers Association (https://iwa-ait.org)
- Anarchistyczne FAQ (http://anarchizm.info) a translation of Anarchist FAQ (https://theanarchistlibrary.org/library/the-anarchist-faq-editorial-collective-an-anarchist-faq)
- Federacja Anarchistyczna (http://federacja-anarchistyczna.pl)
- Związek Syndykalistów Polski (https://zsp.net.pl) (Polish section of IWA-AIT)
- Komitet Obrony Praw Lokatorów (https://lokatorzy.info.pl)
- Solidarity Federation (https://solfed.org.uk)
- Priama Akcia (https://priamaakcia.sk)

Special thanks to `Working Class History <https://twitter.com/wrkclasshistory>`_ for very powerful samples that we could use in our unit tests.
