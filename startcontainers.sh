#!/bin/bash
CONTAINER_NAME=voteswap-mysql
MYSQL_USER=voteswap
MYSQL_PASSWORD=password

if [[ $(docker inspect -f {{.State.Running}} $CONTAINER_NAME 2&> /dev/null) != "true" ]]; then
    echo "Starting ${CONTAINER_NAME}";
    docker run \
        --name ${CONTAINER_NAME} \
        --publish 53306:3306 \
        -e MYSQL_ROOT_PASSWORD=rootpassword \
        -e MYSQL_USER=${MYSQL_USER} \
        -e MYSQL_PASSWORD=${MYSQL_PASSWORD} \
        -v $(pwd)/.mysql_data:/var/lib/mysql \
        -v $(pwd)/mysqlbootstrap:/docker-entrypoint-initdb.d \
        -d \
        mysql:5.7
fi

connect() {
    docker exec $CONTAINER_NAME sh -c \
        "exec mysql --user=${MYSQL_USER} --password=${MYSQL_PASSWORD} -e 'show databases;'" &> /dev/null
}

connect;
available=$?;
until [ $available -eq 0 ]; do
    echo "Waiting for ${CONTAINER_NAME} to come up"
    sleep 1;
    connect;
    available=$?;
done

echo "${CONTAINER_NAME} is running"
