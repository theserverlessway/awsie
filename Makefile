release-docker:
	docker build --no-cache -t flomotlik/awsie -f Dockerfile.release .
	docker push flomotlik/awsie