# Updating

## Requirements

See [installation guide](INSTALL.md#requirements)

## Notices

See [Notices](INSTALL.md#notices)

## Python modules

To update installed modules based on latest Pipfile use this command:

- `pipenv update`  

The virtual environment can be activated with:

- `pipenv shell`

## Running

The following commands that have `manage.py` in them **MUST** use this virtual environment.

#### Environment variables

See [installation guide](INSTALL.md#environment-variables)

#### Database migrations 

You need to update your database schema using django's `makemigrations` command and then apply it using `migrate` command.
- `python manage.py makemigrations`
- `python manage.py migrate --database=default`
- `python manage.py migrate --database=log`

## Caching

See [installation guide](INSTALL.md#caching)

## Celery jobs

See [installation guide](INSTALL.md#celery-jobs)

## Tariff plans

See [installation guide](INSTALL.md#tariff-plans)

## Branches

If this is the first update after [this commit](https://git.respina.net/backend/cgrates-gateway/commit/2801dea79f351d5a4cf2ea82d0a544fb44399d0f), an update for subscriptions' branches is **REQUIRED**. Use `finance_renew_branches` command to update subscriptions' branches. This command can be used to update subscriptions' branches to the current state at any time.  
- ` python manage.py fianace_renew_branches`

## Subscriptions' type

Use `finance_renew_subscription_type` command to update subscriptions' type. This command can be used to update subscriptions' type to the current state at any time.  
- ` python manage.py finance_renew_subscription_type`

## RuntimeConfigs

Use `finance_update_runtime_config` commands to update `RuntimeConfig`:

- `pipenv run python manage.py finance_update_runtime_config`

## Static files

See [installation guide](INSTALL.md#static-files)

## Translations

See [installation guide](INSTALL.md#translations)

## Jobs

See [installation guide](INSTALL.md#jobs)