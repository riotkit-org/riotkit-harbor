
.SILENT:

COMPOSE_PROJECT_NAME = change_name
PREPARE := $(shell test -e .env || cp .env-default .env)
IS_ENV_PRESENT := $(shell test -e .env && echo -n yes)
APP_USER=$(shell whoami)

ifeq ($(IS_ENV_PRESENT), yes)
	include .env
	export $(shell sed 's/=.*//' .env)
endif

SHELL = /bin/bash
COMPOSE_COMPILED_ARGS = $$(for f in $$(ls ./apps/conf|grep -v ".yml.disabled"); do echo "-f ./apps/conf/$${f}"; done)
COMPOSE_ARGS = -p ${COMPOSE_PROJECT_NAME} --project-directory $$(pwd) -f docker-compose.yml ${COMPOSE_COMPILED_ARGS}

# Colors
COLOR_RESET   = \033[0m
COLOR_INFO    = \033[32m
COLOR_COMMENT = \033[33m

## This help screen
help:
	printf "${COLOR_COMMENT}Usage:${COLOR_RESET}\n"
	printf " make [target]\n\n"
	printf "${COLOR_COMMENT}Available targets:${COLOR_RESET}\n"
	awk '/^[a-zA-Z\-\_0-9\.@]+:/ { \
		helpMessage = match(lastLine, /^## (.*)/); \
		if (helpMessage) { \
			helpCommand = substr($$1, 0, index($$1, ":")); \
			helpMessage = substr(lastLine, RSTART + 3, RLENGTH); \
			printf " ${COLOR_INFO}%-16s${COLOR_RESET}\t\t%s\n", helpCommand, helpMessage; \
		} \
	} \
	{ lastLine = $$0 }' $(MAKEFILE_LIST)

## Lists docker-compose args
get_compose_args:
	echo ${COMPOSE_ARGS}

## Starts or updates (if config was changed) the environment
start:
	sudo rm ./data/conf.d/* 2>/dev/null || true # nginx config needs to be recreated on each restart by proxy-gen
	set -x; sudo docker-compose ${COMPOSE_ARGS} up -d
	make _exec_hooks NAME=post-start
	sudo docker-compose ${COMPOSE_ARGS} logs -f

## Stops the environment
stop:
	sudo docker-compose ${COMPOSE_ARGS} down
	make _exec_hooks NAME=post-down

_exec_hooks:
	printf " >> Executing hooks ${NAME}\n"

	if [[ -d ./hooks.d/${NAME}/ ]] && [ ! -z "$(ls -A ./hooks.d/${NAME})" ]; then \
		for f in ./hooks.d/${NAME}/*.sh; do \
			bash $${f}; \
		done \
	fi

## Restart
restart:
	sudo systemctl restart project

## Check status
check_status:
	sudo systemctl status project

## Deployment hook: PRE up
deployment_pre: pull_containers update_all
	make _exec_hooks NAME=deployment-pre

## Update this deployment repository
pull: pull_git pull_containers

pull_git:
	git pull origin master

pull_containers:
	sudo docker-compose ${COMPOSE_ARGS} pull

## Pull image from registry for specified service and rebuild, restart the service (params: SERVICE eg. app_pl.godna-praca)
update_single_service_container:
	sudo docker-compose ${COMPOSE_ARGS} pull ${SERVICE}
	sudo docker-compose ${COMPOSE_ARGS} stop -t 1 ${SERVICE}
	sudo docker-compose ${COMPOSE_ARGS} up --no-start --force-recreate --build ${SERVICE}
	sudo docker-compose ${COMPOSE_ARGS} start ${SERVICE}

## List all repositories
list_repos:
	ls ./apps/repos-enabled | grep .sh | cut -d '.' -f 1

## List all configurations
list_configs:
	ls ./apps/conf | grep .yml | cut -d '.' -f 2

## List enabled configurations
list_configs_enabled:
	ls ./apps/conf | grep .yml | grep -v ".disabled" | cut -d '.' -f 2

## List disabled configurations
list_configs_disabled:
	ls ./apps/conf | grep .yml | grep "disabled" | cut -d '.' -f 2

## List all hosts exposed to the internet
list_all_hosts:
	find ./apps/conf -name '*.yml' | xargs grep 'VIRTUAL_HOST'

## Disable a configuration (APP_NAME=...)
config_disable:
	echo " >> Use APP_NAME eg. make config_disable APP_NAME=iwa-ait"
	mv ./apps/conf/docker-compose.${APP_NAME}.yml ./apps/conf/docker-compose.${APP_NAME}.yml.disabled
	echo " OK, ${APP_NAME} was disabled."

## Enable a configuration (APP_NAME=...)
config_enable:
	echo " >> Use APP_NAME eg. make config_disable APP_NAME=iwa-ait"
	mv ./apps/conf/docker-compose.${APP_NAME}.yml.disabled ./apps/conf/docker-compose.${APP_NAME}.yml
	echo " OK, ${APP_NAME} is now enabled."

## Updates a single application, usage: make update APP_NAME=iwa-ait
update:
	sudo -u "${APP_USER}" make _update APP_NAME=${APP_NAME};\

_update:
	if [[ ! "${APP_NAME}" ]] || [[ ! -f ./apps/repos-enabled/${APP_NAME}.sh ]]; then \
		echo " >> Missing VALID application name, example usage: make update APP_NAME=iwa-ait"; \
		echo " >> Please select one application, choices:"; \
		make list_repos; \
		exit 1; \
	fi

	current_pwd=$$(pwd); post_update() { return 0; };\
	source ./apps/repos-enabled/${APP_NAME}.sh; \
	[[ -d ./apps/www-data/$${GIT_PROJECT_DIR} ]] && sudo chown -R `id -u`:`id -g` ./apps/www-data/$${GIT_PROJECT_DIR}; \
	make __fetch_repository GIT_PROJECT_DIR=$${GIT_PROJECT_DIR} GIT_PASSWORD=$${GIT_PASSWORD} GIT_PROJECT_NAME=$${GIT_PROJECT_NAME} || exit 1; \
	post_update "./apps/www-data/$${GIT_PROJECT_DIR}" || exit 1;\
	cd $${current_pwd} && make __chown_writable_dirs APP_NAME=${APP_NAME}

__chown_writable_dirs:
	echo " >> Preparing write permissions for upload directories for '${APP_NAME}'"
	CONTAINER_USER=${DEFAULT_CONTAINER_USER}; \
	source ./apps/repos-enabled/${APP_NAME}.sh; \
	dirs_to_chown=($${WRITABLE_DIRS//;/ });\
	\
	for writable_dir in "$${dirs_to_chown[@]}"; do \
		echo " >> Making $${CONTAINER_USER} owner of ./apps/www-data/$${GIT_PROJECT_DIR}/$${writable_dir}"; \
		sudo chown -R $${CONTAINER_USER} "./apps/www-data/$${GIT_PROJECT_DIR}/$${writable_dir}" || true; \
	done

## Deploy updates to all applications
update_all:
	echo " >> Deploying all applications"
	make list_repos

	for APP_NAME in $$(make list_repos); do \
		echo " >> Deploying $${APP_NAME}";\
		make update APP_NAME=$${APP_NAME}; \
		if [[ $$? != 0 ]]; then \
			echo " >> !!! Failed deploying $${APP_NAME}";\
			exit 1; \
		fi \
	done

__rm:
	sudo docker-compose ${COMPOSE_ARGS} rm

__fetch_repository:
	echo " >> Updating application at ./apps/www-data/${GIT_PROJECT_DIR}"
	if [[ -d ./apps/www-data/${GIT_PROJECT_DIR}/.git ]]; then \
		cd "./apps/www-data/${GIT_PROJECT_DIR}" || exit 1; \
		echo " >> Setting remote origin"; \
		git remote remove origin 2>/dev/null || true; \
		git remote add origin ${GIT_PROTO}://${GIT_USER}:${GIT_PASSWORD}@${GIT_SERVER}/${GIT_ORG_NAME}/${GIT_PROJECT_NAME}; \
		git pull origin master || exit 1; \
		git remote remove origin 2>/dev/null || true; \
	else \
		echo " >> Cloning..."; \
		git clone ${GIT_PROTO}://${GIT_USER}:${GIT_PASSWORD}@${GIT_SERVER}/${GIT_ORG_NAME}/${GIT_PROJECT_NAME} ./apps/www-data/${GIT_PROJECT_DIR} || exit 1; \
	fi;

## Encrypt the .env-prod file with Ansible Vault (passphrase needs to be stored in ./.vault-password that should be in .gitignore)
encrypt_env_prod:
	echo " >> Encrypting .env file into .env-prod"
	cp .env .env-prod-tmp
	ansible-vault --vault-password-file=$$(pwd)/.vault-password encrypt .env-prod-tmp
	mv .env-prod-tmp .env-prod
