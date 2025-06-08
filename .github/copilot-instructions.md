
when dealing with run commands and docker related commands add docker-compoe.yml to context and relevant dockerfile, .env
run conventions:
 - reset: docker-compose down -v
 - run:  docker-compose up --build -d (automatically runs all parts of app and e2e tests)
 - check logs: docker-compose logs (service_name see in docker-compose.yml)
 - rerun tests: docker-compose up --build -d e2e
 - run backend unit tests cd <full path to backend> && .venv/scripts/activate && pytest 