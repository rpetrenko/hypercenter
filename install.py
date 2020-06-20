# check ports 8080 and 5601 are not taken

# bring up containers
# docker-compose up -d

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