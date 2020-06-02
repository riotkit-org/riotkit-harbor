
.SILENT:

SHELL = /bin/bash
WARN_SLEEP_TIME=10
PIP=pip
SUDO=sudo
DETACH=true

# --- include: env variables from .env
PREPARE := $(shell test -e .env || cp .env-default .env)
IS_ENV_PRESENT := $(shell test -e .env && echo -n yes)

ifeq ($(IS_ENV_PRESENT), yes)
	include .env
	export $(shell sed 's/=.*//' .env)
endif
# -- end of include

# Environment detection (detects if it's production or development basing on "localhost" presence in domains configuration, or ENFORCE_DEBUG_ENVIRONMENT=1)
IS_DEBUG_ENVIRONMENT=$(shell (([[ "${DOMAIN_SUFFIX}" == *".localhost"* ]] || [[ "${MAIN_DOMAIN}" == *"localhost"* ]] || [[ "${ENFORCE_DEBUG_ENVIRONMENT}" == "1" ]]) && echo "1") || echo "0")

# User and group detection. Allows to keep APP_USER and APP_GROUP empty, so the differences in configuration between production and developer environment could be minimized there
USER=$(shell ([[ "${APP_USER}" != "" ]] && echo "${APP_USER}") || ([[ "${SUDO_USER}" != "" ]] && echo "${SUDO_USER}") || whoami)
GROUP_ID=$(shell ([[ "${APP_GROUP_ID}" != "" ]] && echo "${APP_GROUP_ID}") || ([[ "${SUDO_GID}" != "" ]] && echo "${SUDO_GID}") || id -g)

# list all enabled application configurations (docker-compose configuration files)
COMPOSE_COMPILED_ARGS = $$(for f in $$(ls ./apps/conf|grep -v ".yml.disabled"|grep ".yml"); do echo "-f ./apps/conf/$${f}"; done)

# on "localhost" add also all development configurations
COMPOSE_COMPILED_DEV_ARGS = $(shell [[ "${IS_DEBUG_ENVIRONMENT}" == "1" ]] && (for f in $$(ls ./apps/conf.dev|grep -v ".yml.disabled"|grep ".yml"); do echo "-f ./apps/conf.dev/$${f}"; done))
COMPOSE_ARGS = -p ${COMPOSE_PROJECT_NAME} --project-directory $$(pwd) -f docker-compose.yml ${COMPOSE_COMPILED_ARGS} ${COMPOSE_COMPILED_DEV_ARGS}

# Colors
COLOR_RESET   = \033[0m
COLOR_INFO    = \033[32m
COLOR_COMMENT = \033[33m


########### ENVIRONMENT CORE ###########

help: ## This help screen
	@grep -E '^[a-zA-Z\-\_0-9\.@]+:.*?## .*$$' Makefile | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

	@echo ""
	@echo " Environment configuration:"
	@echo "> Main domain: ${MAIN_DOMAIN}${DOMAIN_SUFFIX}"
	@echo "> Debug status (1/0): ${IS_DEBUG_ENVIRONMENT}"
	@echo "> Non-root user that will own git repositories files: ${USER}"
	@echo "> Non-root group id: ${GROUP_ID}"

setup: ## Install requirements for the environment (eg. libraries)
	${SUDO} ${PIP} install -r ./requirements.txt

get_compose_args: ## Lists docker-compose args
	echo ${COMPOSE_ARGS}

# entrypoint for docker-compose command
_call_compose:
	${SUDO} /bin/bash -c 'export IS_DEBUG_ENVIRONMENT=${IS_DEBUG_ENVIRONMENT}; docker-compose ${COMPOSE_ARGS} ${CMD}'

start: ## Starts or updates (if config was changed) the environment (params: DETACH=true/false)
	${SUDO} rm ./data/conf.d/* 2>/dev/null || true # nginx config needs to be recreated on each restart by proxy-gen
	make _clean_up_default_network

	make _call_compose CMD="up -d"
	${SUDO} make _exec_hooks NAME=post-start

	if [[ "${DETACH}" != "true" ]]; then \
		make _call_compose CMD="logs -f"; \
	fi

stop: ## Stops the environment
	make _call_compose CMD="down"
	make _exec_hooks NAME=post-down

_clean_up_default_network:
	printf " >> Cleaning up silently the default network\n"
	${SUDO} docker network rm $(docker network ls -f name=${COMPOSE_PROJECT_NAME} -q) 2>/dev/null || true

_exec_hooks:
	printf " >> Executing hooks ${NAME}\n"

	if [[ -d ./hooks.d/${NAME}/ ]] && [ ! -z "$$(ls -A ./hooks.d/${NAME}/ | grep '.sh' | grep -v '.disabled')" ]; then \
		export IS_DEBUG_ENVIRONMENT=${IS_DEBUG_ENVIRONMENT};\
		for f in ./hooks.d/${NAME}/*.sh; do \
			bash $${f}; \
		done \
	fi

deployment_pre: __assert_has_root_permissions pull_containers update_all render_templates ## Deployment hook: PRE up
	make _exec_hooks NAME=deployment-pre

pull: _root_session pull_git pull_containers ## Update this deployment repository

pull_git:
	git pull origin master

update_single_service_container: _root_session ## Pull image from registry for specified service and rebuild, restart the service (params: SERVICE eg. app_pl.godna-praca)
	make _call_compose CMD="pull ${SERVICE}"
	make _call_compose CMD="stop -t 1 ${SERVICE}"
	make _call_compose CMD="up --no-start --force-recreate --build ${SERVICE}"
	make _call_compose CMD="start ${SERVICE}"

render_templates: ## Render all templates using .env file
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


########### GIT-VOLUME REPOSITORIES ###########

__rm:
	make _call_compose CMD="rm"


########### BACKUP RECOVERY ###########

recover_from_backup: _root_session ## Recover services from a backup (Use cases: Moving from dev to prod, Recovery from failure, Migrating from server to server)
	echo " >> !!! WARNING !!!: In ${WARN_SLEEP_TIME} seconds selected or ALL services will be restored from backup with a ${BACKUPS_RECOVERY_PLAN} recovery plan"
	echo " >> If this is not what you want, just do CTRL+C NOW!"
	sleep ${WARN_SLEEP_TIME}
	make _call_compose CMD="exec ${BACKUPS_CONTAINER} bahub recover ${BACKUPS_RECOVERY_PLAN}"


########### ANSIBLE ###########

encrypt_env_prod: ## Encrypt the .env-prod file with Ansible Vault (passphrase needs to be stored in ./.vault-password that should be in .gitignore)
	echo " >> Encrypting .env file into .env-prod"
	cp .env .env-prod-tmp
	ansible-vault --vault-password-file=$$(pwd)/.vault-password encrypt .env-prod-tmp
	mv .env-prod-tmp .env-prod

edit_env_prod: ## Edit production environment configuration (.env.prod)
	ansible-vault --vault-password-file=$$(pwd)/.vault-password edit .env-prod

########### DOCUMENTATION ###########

build_docs: ## Build documentation
	cd ./docs && make html


########### PROJECT SPECIFIC ###########
