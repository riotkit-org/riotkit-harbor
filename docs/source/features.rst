.. _features:

Features
========

Service discovery with SSL
--------------------------

Whenever you run a new application, even without restarting the whole environment, the **gateway_proxy_gen** container
is being notified about it and creates an nginx cnofiguration to expose your application. **gateway_letsencrypt** is also
notified and generates a SSL configuration, right after nginx is ready.

Step-by-step schema:

1. **gateway_proxy_gen** listens to docker events
2. **gateway_proxy_gen** generates nginx.conf for each TAGGED service in docker network (VIRTUAL_HOST, VIRTUAL_PORT, LETSENCRYPT_HOST and LETSENCRYPT_EMAIL must be present)
3. **gateway_letsencrypt** generates SSL certificates for recently added domains
4. **gateway** is being reloaded and uses new nginx.conf with SSL certificates

FAQ:

1. Multiple domains: Separate them by comma
2. For advanced usages see: docker-gen_ documentation
3. I need to modify nginx.conf, how to? It's easy. There are two solutions:

   a) Create a file with domain name in the **./containers/nginx/vhost.d** directory

    Example "test.mydomain.org" file:

    .. code:: yaml

        ## Start of configuration add by letsencrypt container
        location ^~ /.well-known/acme-challenge/ {
            auth_basic off;
            allow all;
            root /usr/share/nginx/html;
            try_files $uri =404;
            break;
        }
        ## End of configuration add by letsencrypt container

        proxy_read_timeout 120s;


    b) Modify directly the template from which the nginx.conf is created



.. _docker-gen: https://github.com/jwilder/docker-gen

Services dashboard
------------------

Often non-technical people are not aware of what services are actually hosted. There we resolve this problem
with an automatically generated list of running web-apps.

Applications needs to be tagged with docker labels, example:

.. code:: yaml

    org.docker.services.dashboard.enabled: true
    org.docker.services.dashboard.description: 'Dashboard - a list of all hosted websites running on this network'
    org.docker.services.dashboard.icon: 'pe-7s-browser'
    org.docker.services.dashboard.only_for_admin: false

Sending e-mails
---------------

Send e-mails directly or through a middle server, just by sending them on "smtp_server:25" without any authorization.
You can use any external SMTP, your own, a gmail account, or other.

.. code:: yaml

    SMARTHOST_ADDRESS=your-server.org    # your SMTP relay server address
    SMARTHOST_PORT=587
    SMARTHOST_USER=login@your-server.org
    SMARTHOST_PASSWORD=
    SMARTHOST_ALIASES=*    # forward all e-mails, you can put here eg. allowed recipient domains


If you make values empty, then the service will send mails directly.

