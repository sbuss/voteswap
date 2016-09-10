#!/bin/bash
docker run \
    --name mysql-voteswap \
    --publish 3306:3306 \
    -e MYSQL_ROOT_PASSWORD=rootpassword \
    -e MYSQL_USER=voteswap \
    -e MYSQL_PASSWORD=password \
    -v $(pwd)/.mysql_data:/var/lib/mysql \
    -v $(pwd)/mysqlbootstrap:/docker-entrypoint-initdb.d \
    -d \
    mysql:5.7

docker exec mysql-voteswap sh -c "exec mysql -uroot -prootpassword -e 'show databases;'";
available=$?;
until [ $available -eq 0 ]; do
    sleep 1;
    docker exec mysql-voteswap sh -c "exec mysql -uroot -prootpassword -e 'show databases;'";
    available=$?;
done
