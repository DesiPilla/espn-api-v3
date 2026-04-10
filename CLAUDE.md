# Project Setup

## Virtual Environment

Always activate the virtual environment before running any terminal commands:

```
pyenv activate espn-api-v3
```

After activating the virtual environment, always load environment variables:

```
source .env
```

## Running the App

To launch the React/Django app (in a separate terminal, also requires the virtual environment):

```
python manage.py collectstatic --no-input && python manage.py runserver 8001
```
