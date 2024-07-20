# Variables for Docker
IMAGE_NAME = fix_blue_screened_vms
TAG = latest
DOCKERFILE_PATH = .
REGISTRY = your_registry
REPO = your_repo

# Load environment variables from .env file
include .env
export $(shell sed 's/=.*//' .env)

# Variables for CLI commands
COMMAND = pipenv run python -m cloudpurge

# Docker build, tag, and push
build:
	docker build -t $(IMAGE_NAME):$(TAG) $(DOCKERFILE_PATH)

tag:
	docker tag $(IMAGE_NAME):$(TAG) $(REGISTRY)/$(REPO)/$(IMAGE_NAME):$(TAG)

push: tag
	docker push $(REGISTRY)/$(REPO)/$(IMAGE_NAME):$(TAG)

clean:
	docker rmi $(IMAGE_NAME):$(TAG)
	docker rmi $(REGISTRY)/$(REPO)/$(IMAGE_NAME):$(TAG)

# Install dependencies
install-deps:
	pipenv install pyvmomi pillow paramiko python-dotenv

# CLI commands
create-role:
	$(COMMAND) create-role --role-name $(ROLE_NAME)

assign-role:
	$(COMMAND) assign-role --role-name $(ROLE_NAME) --user $(TARGET_USER) --datacenter $(DATACENTER_NAME)

list-vms:
	$(COMMAND) inventory

check-bluescreen:
	$(COMMAND) check-bluescreen

inventory-bluescreen:
	$(COMMAND) inventory-bluescreen

list-user-roles:
	$(COMMAND) list-user-roles --user $(TARGET_USER)

check-user-role:
	$(COMMAND) check-user-role --user $(TARGET_USER) --role-name $(ROLE_NAME)

# Full pipeline: build, tag, and push
all: build push

.PHONY: build tag push clean all create-role assign-role list-vms check-bluescreen inventory-bluescreen install-deps list-user-roles check-user-role
