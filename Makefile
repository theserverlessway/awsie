release-docker:
	docker build --no-cache -t flomotlik/awsie -f Dockerfile.release .
	docker push flomotlik/awsie

release-pypi:
	docker-compose run awsie bash -c "python setup.py sdist bdist_wheel && pandoc --from=markdown --to=rst --output=build/README.rst README.md && twine upload dist/*"

release:
	release-pypi release-docker

build-dev:
	docker-compose build awsie

clean:
	rm -fr dist build awsie.egg-info .pytest_cache

dev: build-dev
	docker-compose run awsie bash

test:
	pycodestyle .
	pyflakes .
	grep -r 'print(' awsie; [ "$$?" -gt 0 ]
	py.test --cov=awsie tests