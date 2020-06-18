# Hypervisor Manager Inventory

## Setup
* create .env file to set env vars for docker-compose; set all passwords
```editorconfig
POSTGRES_PASSWORD=<some-password>
POSTGRES_DB=<some-db-name>
SECRET_KEY=<some-django-secret-key>
DJANGO_SUPERUSER=admin
DJANGO_SUPERPASS=<some-admin-password>
DJANGO_HOST=0.0.0.0
DJANGO_PORT=8080
```

* verify the output of docker-compose with substituted environment variables
```bash
docker-compose config
```