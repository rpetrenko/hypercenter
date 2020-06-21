# Hypervisor Manager Inventory

## Setup in 3 steps
1. create .env file inside checked out repository with the following variables
    ```editorconfig
    SUPERPASS=<some-admin-and-db-password>
    PG_DB=<some-db-name>
    SECRET_KEY=<some-django-secret-key>
    WEB_PORT=8080
    ```

1. verify the output of docker-compose with substituted environment variables
    ```bash
    docker-compose config
    ```

1. run installer
    ```bash
    python3 -m venv venv
    . venv/bin/activate
    pip install -r requirements.txt
    ./install.py
    ```
    
## How to use
* the last step will bring up all containers, verify their status and populate database with sample data. Open [HyperManager dashboard](http://localhost:5601/s/test/app/kibana#/dashboard/34bc5770-b352-11ea-b12b-a5d0f6ee8adb) to view sample dashboard

* login to [django admin site](http://localhost:8080/admin/) with username *admin* and password set in .env for *SUPERPASS* variable

* delete sample data for HyperManagers and add your Vcenters. 
 
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