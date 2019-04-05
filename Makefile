
.SILENT:

PREPARE := $(shell test -e .env || cp .env-default .env)
IS_ENV_PRESENT := $(shell test -e .env && echo -n yes)
WARN_SLEEP_TIME=10

ifeq ($(IS_ENV_PRESENT), yes)
	include .env
	export $(shell sed 's/=.*//' .env)
endif

# Environment detection (detects if it's production or development basing on "localhost" presence in domains configuration, or ENFORCE_DEBUG_ENVIRONMENT=1)
IS_DEBUG_ENVIRONMENT=$(shell (([[ "${DOMAIN_SUFFIX}" == *".localhost"* ]] || [[ "${MAIN_DOMAIN}" == *"localhost"* ]] || [[ "${ENFORCE_DEBUG_ENVIRONMENT}" == "1" ]]) && echo "1") || echo "0")

# User and group detection. Allows to keep APP_USER and APP_GROUP empty, so the differences in configuration between production and developer environment could be minimized there
USER=$(shell ([[ "${APP_USER}" != "" ]] && echo "${APP_USER}") || ([[ "${SUDO_USER}" != "" ]] && echo "${SUDO_USER}") || whoami)
GROUP_ID=$(shell ([[ "${APP_GROUP_ID}" != "" ]] && echo "${APP_GROUP_ID}") || ([[ "${SUDO_GID}" != "" ]] && echo "${SUDO_GID}") || id -g)

SHELL = /bin/bash
COMPOSE_COMPILED_ARGS = $$(for f in $$(ls ./apps/conf|grep -v ".yml.disabled"); do echo "-f ./apps/conf/$${f}"; done)
COMPOSE_ARGS = -p ${COMPOSE_PROJECT_NAME} --project-directory $$(pwd) -f docker-compose.yml ${COMPOSE_COMPILED_ARGS}

# Colors
COLOR_RESET   = \033[0m
COLOR_INFO    = \033[32m
COLOR_COMMENT = \033[33m

PIP=pip
SUDO=sudo


########### ENVIRONMENT CORE ###########

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

	echo ""
	echo " Environment configuration:"
	echo "> Main domain: ${MAIN_DOMAIN}${DOMAIN_SUFFIX}"
	echo "> Debug status (1/0): ${IS_DEBUG_ENVIRONMENT}"
	echo "> Non-root user that will own git repositories files: ${USER}"
	echo "> Non-root group id: ${GROUP_ID}"

## Install requirements for the environment (eg. libraries)
setup:
	${SUDO} ${PIP} install -r ./requirements.txt

## Lists docker-compose args
get_compose_args:
	echo ${COMPOSE_ARGS}

# entrypoint for docker-compose command
_call_compose:
	${SUDO} /bin/bash -c 'export IS_DEBUG_ENVIRONMENT=${IS_DEBUG_ENVIRONMENT}; docker-compose ${COMPOSE_ARGS} ${CMD}'

## Starts or updates (if config was changed) the environment
start:
	${SUDO} rm ./data/conf.d/* 2>/dev/null || true # nginx config needs to be recreated on each restart by proxy-gen
	make _call_compose CMD="up -d"
	${SUDO} make _exec_hooks NAME=post-start

	if [[ "${DETACH}" != "true" ]]; then \
		make _call_compose CMD="logs -f"; \
	fi

## Stops the environment
stop:
	make _call_compose CMD="down"
	make _exec_hooks NAME=post-down

_exec_hooks:
	printf " >> Executing hooks ${NAME}\n"

	if [[ -d ./hooks.d/${NAME}/ ]] && [ ! -z "$$(ls -A ./hooks.d/${NAME}/ | grep '.sh')" ]; then \
		export IS_DEBUG_ENVIRONMENT=${IS_DEBUG_ENVIRONMENT};\
		for f in ./hooks.d/${NAME}/*.sh; do \
			bash $${f}; \
		done \
	fi

_root_session:
	sudo true

## Restart
restart: _root_session
	${SUDO} systemctl restart project

## Check status
check_status: _root_session
	${SUDO} systemctl status project

## Deployment hook: PRE up
deployment_pre: __assert_has_root_permissions pull_containers update_all render_templates
	make _exec_hooks NAME=deployment-pre

## Update this deployment repository
pull: _root_session pull_git pull_containers

pull_git:
	git pull origin master

pull_containers: _root_session
	make _call_compose CMD="pull"

## Pull image from registry for specified service and rebuild, restart the service (params: SERVICE eg. app_pl.godna-praca)
update_single_service_container: _root_session
	make _call_compose CMD="pull ${SERVICE}"
	make _call_compose CMD="stop -t 1 ${SERVICE}"
	make _call_compose CMD="up --no-start --force-recreate --build ${SERVICE}"
	make _call_compose CMD="start ${SERVICE}"

## Render all templates using .env file
render_templates:
	echo " >> Rendering templates from ./containers/templates/source"
	found=$$(find ./containers/templates/source -type f -name '*.j2'); \
	for template in $${found[@]}; do \
		file_path=$${template/\/templates\/source/\/templates\/compiled}; \
		target_path=$$(dirname $${file_path}); \
		\
		echo " .. Rendering $${template}"; \
		mkdir -p $${target_path}; \
		source .env; j2 $${template} > $${file_path/.j2/}; \
	done


########### YAML SERVICES ###########

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

########### MAINTENANCE MODE ###########

## Turn on maintenance on on all websites
maintenance_on:
	sudo touch ./data/maintenance-mode/on

## Turn off maintenance mode on all websites
maintenance_off:
	sudo rm -f ./data/maintenance-mode/on

########### GIT-VOLUME REPOSITORIES ###########

## List all repositories
list_repos:
	ls ./apps/repos-enabled | grep .sh | cut -d '.' -f 1

## Updates a single application, usage: make update APP_NAME=iwa-ait
update: __assert_has_root_permissions
	make _update_existing_directory_permissions APP_NAME=${APP_NAME}
	${SUDO} -u "${USER}" make _update APP_NAME=${APP_NAME}
	make __chown_writable_dirs APP_NAME=${APP_NAME}

_update_existing_directory_permissions: __assert_has_root_permissions
	echo " >> Updating existing directory permissions"
	source ./apps/repos-enabled/${APP_NAME}.sh; \
	[[ -d ./apps/www-data/$${GIT_PROJECT_DIR} ]] && set -x && chown -R ${USER}:${GROUP_ID} ./apps/www-data/$${GIT_PROJECT_DIR}; \
	exit 0

_update: __assert_not_root
	if [[ ! "${APP_NAME}" ]] || [[ ! -f ./apps/repos-enabled/${APP_NAME}.sh ]]; then \
		echo " >> Missing VALID application name, example usage: make update APP_NAME=iwa-ait"; \
		echo " >> Please select one application, choices:"; \
		make list_repos; \
		exit 1; \
	fi

	current_pwd=$$(pwd); post_update() { return 0; };\
	source ./apps/repos-enabled/${APP_NAME}.sh; \
	make __fetch_repository GIT_PROJECT_DIR=$${GIT_PROJECT_DIR} GIT_PASSWORD=$${GIT_PASSWORD} GIT_PROJECT_NAME=$${GIT_PROJECT_NAME} || exit 1; \
	post_update "./apps/www-data/$${GIT_PROJECT_DIR}" || exit 1;

# running as root
__chown_writable_dirs: __assert_has_root_permissions
	echo " >> Preparing write permissions for upload directories for '${APP_NAME}'"
	CONTAINER_USER=${DEFAULT_CONTAINER_USER}; \
	source ./apps/repos-enabled/${APP_NAME}.sh; \
	dirs_to_chown=($${WRITABLE_DIRS//;/ });\
	\
	for writable_dir in "$${dirs_to_chown[@]}"; do \
		echo " >> Making $${CONTAINER_USER} owner of ./apps/www-data/$${GIT_PROJECT_DIR}/$${writable_dir}"; \
		chown -R $${CONTAINER_USER} "./apps/www-data/$${GIT_PROJECT_DIR}/$${writable_dir}" || true; \
	done

__assert_not_root:
	if [[ "$$(id -u)" == "0" ]]; then \
		id -u;\
		echo " This task cannot work with root privileges"; \
		exit 1; \
	fi

__assert_has_root_permissions:
	if [[ "$$(id -u)" != "0" ]]; then \
		id -u;\
		echo " Root permissions required"; \
		exit 1; \
	fi

## Deploy updates to all applications
update_all: __assert_has_root_permissions
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
	make _call_compose CMD="rm"

__fetch_repository: __assert_not_root
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


########### BACKUP RECOVERY ###########

## Recover services from a backup (Use cases: Moving from dev to prod, Recovery from failure, Migrating from server to server)
recover_from_backup: _root_session
	echo " >> !!! WARNING !!!: In ${WARN_SLEEP_TIME} seconds selected or ALL services will be restored from backup with a ${BACKUPS_RECOVERY_PLAN} recovery plan"
	echo " >> If this is not what you want, just do CTRL+C NOW!"
	sleep ${WARN_SLEEP_TIME}
	make _call_compose CMD="exec ${BACKUPS_CONTAINER} bahub recover ${BACKUPS_RECOVERY_PLAN}"


########### ANSIBLE ###########

## Encrypt the .env-prod file with Ansible Vault (passphrase needs to be stored in ./.vault-password that should be in .gitignore)
encrypt_env_prod:
	echo " >> Encrypting .env file into .env-prod"
	cp .env .env-prod-tmp
	ansible-vault --vault-password-file=$$(pwd)/.vault-password encrypt .env-prod-tmp
	mv .env-prod-tmp .env-prod


########### DOCUMENTATION ###########

## Build documentation
build_docs:
	cd ./docs && make html


########### PROJECT SPECIFIC ###########
