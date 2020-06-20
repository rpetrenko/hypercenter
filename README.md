# Hypervisor Manager Inventory

## Setup
* create .env file to set env vars for docker-compose; set all passwords
```editorconfig
SUPERPASS=<some-admin-and-db-password>
PG_DB=<some-db-name>
SECRET_KEY=<some-django-secret-key>
WEB_PORT=8080
```

* verify the output of docker-compose with substituted environment variables
```bash
docker-compose config
```

## Test


## Develop
* create python virtual env, and install packages
```bash
python3 -m venv venv
. venv/bin/activate
pip install -r requirements.txt
```

* login to django container
```bash
docker exec -it hypercenter_web_1 /bin/bash
 ```

* create/populate/rebuild elasticsearch indeces
```bash
 docker exec hypercenter_web_1 python manage.py search_index --create -f
 docker exec hypercenter_web_1 python manage.py search_index --populate -f
 docker exec hypercenter_web_1 python manage.py search_index --rebuild -f
``` 
 
## Debug
* verify elasticsearch search is up and running from django container
```bash
docker exec hypercenter_web_1 curl http://elasticsearch:9200
```

## Load fake data
* load vcenters
```bash
docker exec hypercenter_web_1 python manage.py loaddata hyper/fixtures/vcenters.json
```