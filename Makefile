release-docker:
	docker build --no-cache -t flomotlik/awsie -f Dockerfile.release .
	docker push flomotlik/awsie


release-pypi: build
	docker-compose run awsie twine upload dist/*

release: release-pypi release-docker

build: clean build-dev
	docker-compose run awsie python setup.py sdist bdist_wheel
	docker-compose run awsie pandoc --from=markdown --to=rst --output=build/README.rst README.md

build-dev:
	docker-compose build awsie

clean:
	rm -fr dist

dev: build-dev
	docker-compose run awsie bash
