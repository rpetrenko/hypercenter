# check ports 8080 and 5601 are not taken

# bring up containers
# docker-compose up -d

# assert all 4 containers are running
# CONTAINER ID        IMAGE                                                 COMMAND                  CREATED             STATUS              PORTS                    NAMES
# 85dc2deb18a4        hypercenter_web                                       "python manage.py ru…"   5 seconds ago       Up 4 seconds        0.0.0.0:8080->8080/tcp   hypercenter_web_1
# 52164aeceb1d        postgres:alpine                                       "docker-entrypoint.s…"   6 seconds ago       Up 5 seconds        5432/tcp                 hypercenter_db_1
# 855715c9babf        docker.elastic.co/elasticsearch/elasticsearch:7.5.1   "/usr/local/bin/dock…"   6 seconds ago       Up 5 seconds        9200/tcp, 9300/tcp       hypercenter_elasticsearch_1
# 3b9d3c24de13        docker.elastic.co/kibana/kibana:7.5.2                 "/usr/local/bin/dumb…"   6 seconds ago       Up 5 seconds        0.0.0.0:5601->5601/tcp   hypercenter_kibana_1


# verify django is up
# curl localhost:8080

# verify from web container that elasticsearch is running
# docker-compose run --rm web curl hypercenter_elasticsearch_1:9200
# or
# docker exec hypercenter_web_1 curl http://elasticsearch:9200

# kibana is up
# curl localhost:5601/app/kibana

# apply django migrations
# docker-compose run --rm web python manage.py migrate

# verify admin user can login
# http://localhost:8080/admin