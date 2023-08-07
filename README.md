# chat app back-end API

## Development setup

### Install virtual environment

- Install [poetry](https://python-poetry.org/docs/#installation) on your machine
- You will need Python version 3.10 for this project
- Go into project directory and install all packages with **poetry**:
    ```
    poetry install
    ```

  This will create a new virtual environment and install all project dependencies there

- Configure your IDE of choice to use newly created virtual environment

### Configuring local database

Make sure you have **postgresql** running on your system at standard port 5432

Create user `test` with password `test`
Create database named `test` with owner `test`
Make sure your `test` user can create new databases (for testing)


### Commands

Run development server:

`python manage.py runserver`

or

`./manage.py runserver`

### Database migrations

Automatically generate new migration:

`alembic revision --autogenerate -m "Added User model"`

Create migration for manual editing:

`alembic revision -m "Added User model"`

Apply all migrations:

`alembic upgrade head`

Apply specific migration:

`alembic upgrade version_number`
