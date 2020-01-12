#!/bin/sh
echo "$DATABASE"
if [ "$DATABASE" = "postgres" ]
then
    echo "Waiting for postgres..."
    nc -z $SQL_HOST $SQL_PORT;
    while ! nc -z $SQL_HOST $SQL_PORT; do
      sleep 0.1
    done

    echo "PostgreSQL started"
fi

exec "$@"