i need to make a guide to claude code for a style of working with single-file docker compose.
I also need to make an experiment sandbox so claude code can test these.

style:
look at ../holepunch/docker-compose.yml for a working example
build commands go in an inline dockerfile and are just for dependencies
heredoc style works ok with python but have to be careful with indents and quoting
indentation has to match

guide for running:
need to know to use docker compose not docker-compose
docker-compose doesn't work on my machine, docker compose instead
docker compose restart doesn't usally actually pick up changes have to docker compose down and docker comopse up
best way is to docker compose up -d and docker compose logs separately

make a test plan:
make a test bench docker compose with all the pitfalls or broken examples to try
write a plan to confirm each of the hypotheses
confirm each of the hypotheses by modifying the file and then change it
