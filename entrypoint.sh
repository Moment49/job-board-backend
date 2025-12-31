#!/bin/sh

echo 'Waiting for postgres...'

while ! nc -z $DB_HOSTNAME $DB_PORT; do
    sleep 0.1
done

echo 'PostgreSQL started'

echo 'Running migrations...'
python manage.py makemigrations
python manage.py migrate
python manage.py create_role_groups

# echo 'Collecting static files...'
# python manage.py collectstatic --no-input

exec "$@"