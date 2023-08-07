#!/bin/sh

alembic upgrade head
gunicorn --config config/gunicorn.conf.py
