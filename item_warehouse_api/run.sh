#!/usr/bin/with-contenv bashio

DATABASE_URL_IN=$(bashio::config 'database_url')
DATABASE_USERNAME_IN=$(bashio::config 'database_username')
DATABASE_PASSWORD_IN=$(bashio::config 'database_password')
DATABASE_DRIVER_NAME_IN=$(bashio::config 'database_driver_name')
DATABASE_HOST_IN=$(bashio::config 'database_host')
DATABASE_PORT_IN=$(bashio::config 'database_port')
DATABASE_NAME_IN=$(bashio::config 'database_name')


if [[ -z "${DATABASE_URL-}" ]]
then
    export DATABASE_URL=${DATABASE_URL_IN}
fi

if [[ -z "${DATABASE_USERNAME-}" ]]
then
    export DATABASE_USERNAME=${DATABASE_USERNAME_IN}
fi

if [[ -z "${DATABASE_PASSWORD-}" ]]
then
    export DATABASE_PASSWORD=${DATABASE_PASSWORD_IN}
fi

if [[ -z "${DATABASE_DRIVER_NAME-}" ]]
then
    export DATABASE_DRIVER_NAME=${DATABASE_DRIVER_NAME_IN}
fi

if [[ -z "${DATABASE_HOST-}" ]]
then
    export DATABASE_HOST=${DATABASE_HOST_IN}
fi

if [[ -z "${DATABASE_PORT-}" ]]
then
    export DATABASE_PORT=${DATABASE_PORT_IN}
fi

if [[ -z "${DATABASE_NAME-}" ]]
then
    export DATABASE_NAME=${DATABASE_NAME_IN}
fi


uvicorn main:app \
--host 0.0.0.0 \
--port 8002
