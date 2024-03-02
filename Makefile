DOCKER_TAG := ynufes-nginx-staging
GAR_LOCATION := asia-northeast1-docker.pkg.dev/ynufes-hp-cloudrun/staging/nginx:latest

.PHONY: build

build:
	docker build -t $(DOCKER_TAG) .
	docker tag $(DOCKER_TAG):latest $(GAR_LOCATION)

.PHONY: push

push:
	docker push $(GAR_LOCATION)

.PHONY: apply-cloudrun

apply-cloudrun:
	gcloud run services replace service.yaml
