#!/bin/bash

branches=("os-1 5461 8011" "os-2 5462 8012" "os-3 5463 8013" "os-4 5464 8014")

settings_development=FusionIIIT/Fusion/settings/development.py

for branch in "${branches[@]}"
do
    IFS=' ' read -r name db_port app_port <<< "$branch"
    echo "Cloning $name"

	cp -r main "$name"
	cd "$name"
	git checkout -b "$name" origin/"$name"
	git fetch origin "$name"
	git pull
	sed -i "s/5432:5432/$db_port:$db_port/" docker-compose.yml
	sed -i "s/8000:8000/$app_port:$app_port/" docker-compose.yml
	sed -i "s/8000/$app_port/" docker-compose.yml
	sed -i "s/8000/$app_port/" Dockerfile
    sed -i "s/ALLOWED_HOSTS *= *\[ *\]/ALLOWED_HOSTS = \['\*'\]/" $settings_development
	sed -i "/DATABASES = {/,/}/{s|'NAME': 'fusionlab',|'NAME': 'fusiondb',|; s|'HOST': 'localhost',|'HOST': os.environ.get(\"DB_HOST\"),|; s|'USER': 'fusion_admin',|'USER': 'fusionuser',|; s|'PASSWORD': 'hello123',|'PASSWORD': 'password',|}" $settings_development
	docker-compose up -d
#   sudo docker exec -i "$name"_db_1 psql -U fusionuser -d fusiondb < ../../fusiondb_07feb23.sql
	cd ..

    echo "Completed cloning $name"
done