# installation

## Requirements
- `Python 3.8.5` or higher
- `Postgres 12.2` or higher
- `Redis 6.0.2` or higher
- `CGRateS 0.10.0` from [here](http://pkg.cgrates.org/deb/v0.10/cgrates_0.10.0_amd64.deb)
- `gettext` package for operating system
- `pipenv` module for `Python`

## Pre-Installation
* After installing `Postgres`, create a user and a database for `CGRateS`:  
    - `CREATE ROLE role_name WITH LOGIN ENCRYPTED PASSWORD 'password1';`
    - `CREATE DATABASE db_name OWNER =  role_name;`
    - `ALTER USER database_user CREATEDB;`
* `CGRateS` rates schema (`tp_rates` in `/usr/share/cgrates/storage/mysql/create_tariffplan_tables.sql`) for `MariaDB` should be altered to this:
```
DROP TABLE IF EXISTS `tp_rates`;
CREATE TABLE `tp_rates` (
  `id` int(11) NOT NULL AUTO_INCREMENT,
  `tpid` varchar(64) NOT NULL,
  `tag` varchar(64) NOT NULL,
  `connect_fee` decimal(14,2) NOT NULL,
  `rate` decimal(14,2) NOT NULL,
  `rate_unit` varchar(16) NOT NULL,
  `rate_increment` varchar(16) NOT NULL,
  `group_interval_start` varchar(16) NOT NULL,
  `created_at` TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_tprate` (`tpid`,`tag`,`group_interval_start`),
  KEY `tpid` (`tpid`),
  KEY `tpid_rtid` (`tpid`,`tag`)
);
```
* `CGRateS` rates schema (`tp_rates` in `/usr/share/cgrates/storage/postgres/create_tariffplan_tables.sql`) for `PostgreSQL` should be altered to this:

```
DROP TABLE IF EXISTS tp_rates;
CREATE TABLE tp_rates (
  id SERIAL PRIMARY KEY,
  tpid VARCHAR(64) NOT NULL,
  tag VARCHAR(64) NOT NULL,
  connect_fee NUMERIC(14,2) NOT NULL,
  rate NUMERIC(14,2) NOT NULL,
  rate_unit VARCHAR(16) NOT NULL,
  rate_increment VARCHAR(16) NOT NULL,
  group_interval_start VARCHAR(16) NOT NULL,
  created_at TIMESTAMP WITH TIME ZONE,
  UNIQUE (tpid, tag, group_interval_start)
);
CREATE INDEX tprates_tpid_idx ON tp_rates (tpid);
CREATE INDEX tprates_idx ON tp_rates (tpid,tag);
```

* `CGrateS Service` and `CGG` must have matching timezone. Default and accepted timezone is `UTC`

## Notices

#### Dos

- Do create a folder under path `cgg/` having the same name with `CGRATES_GATEWAY_STATIC_DIRS` variable from `local.env`
- Do grant `CREATEDB` permission to database user for unit tests to work using `ALTER USER database_user CREATEDB;`

#### Do NOTs

- DO NOT copy and replace your existing `local.env` from `local.example.env`. just check the difference between them and change what's necessary.
- Do NOT delete any files under this folder pattern or it may lead to major problems in database version control:
`cgg/apps/*/migrations`.
- Do NOT edit any file with `.py` extension. All environment related settings are stored in one file (`local.env`).
- Do NOT rerun `loaddata` commands from this guide.
- Do NOT use the same string for `CGRATES_GATEWAY_STATIC_DIRS` and `CGRATES_GATEWAY_STATIC_ROOT` in `local.env`
- Do NOT create virtual environment under `root` user.

## Python modules

Use this commands to install python and required modules automatically:

- `pipenv install`    

The virtual environment can be activated with:

- `pipenv shell`


## Running

The following commands that have `manage.py` in them **MUST** use this virtual environment.

#### Environment variables

Copy `local.example.env` from `/cgg/settings` to `cgg/settings/local.env` and edit it using `vim`. This file contains all the local variables that `CGG` needs to run including database credentials, URLs and tokens to external APIs and etc. 

- `cp cgg/settings/local.example.env cgg/settings/local.env`
- Edit `local.env` to match environment variables and set them using `set -a && . ./cgg/settings/local.env && set +a`
- Important note: When using `uWSGI` and systemd to run `CGG` set environment variables before `ExecStart` using `EnvironmentFile=/path/to/cgrates/cgg/settings/local.env`

#### Database migrations and initial data

First, you need to create/update database schema using django's `makemigrations` command and then apply it using `migrate` command. Two tables in `CGG` database needs to be prepopulated. You can do this using predefined `fixtures`.

- `python manage.py makemigrations`
- `python manage.py migrate --database=default`
- `python manage.py migrate --database=log`
- `python manage.py loaddata tax`
- `python manage.py loaddata packages`

## Caching

`CGG` uses a `redis` to cache responses from `CGRateS`. For the caching layer to work properly these variable must be set before running:

- `CGRATES_GATEWAY_REDIS_HOST`
- `CGRATES_GATEWAY_REDIS_PORT`
- `CGRATES_GATEWAY_CACHE_DATABASE`
- `CGRATES_GATEWAY_CACHE_PREFIX`

## Celery jobs

`CGG` uses celery to handle sending notifications to trunk backend. Use this command after setting local environment variables:

- `celery -A cgg worker -l info`

## Static files

Copy all static file from all folders to base folder using `collectstatic` command.

- `python manage.py collectstatic`

## Translations

`CGG` uses `fa` as the default language. To change the translations for a message edit `cgg/locale/fa/LC_MESSAGES/django.po`. To compile translated messages you can use django's `complemessages` command 

- `python manage.py compilemessages`

## Super user

To create a super user use `createsuperuser` command:

- `python manage.py createsuperuser`

## Tariff plans

Initialize `CGRateS` and then import destinations, tariffs and branches only in this order.

#### Initialization

`CGRateS` needs a default charger and supplier profile to work properly. Also some actions in our system needs calling a url from `CGRateS`, for this to work we need to set `call_url` actions in `CGRateS`. We provide a custom command to initialize these data in `CGRateS`.

- `python manage.py finance_init_cgrates`

#### Destinations

To import destinations from a `JSON` file use `finance_import_destinations` custom command.
 - `python manage.py finance_import_destinations [file_path]`  
 - e.g. `python manage.py finance_import_destinations /usr/share/dest.json`     
 
This command uses one mandatory argument named `file_path`. `file_path` is the absolute path of `JSON` file that contains all destination objects. This file must be structured like this:

```
[
    {
        "prefix": "020",
        "name": "Other",
        "country_code": "IRN",
        "code": "landline_national",
    },
    {
        "prefix": "021",
        "name": "Tehran",
        "country_code": "IRN",
        "code": "landline_national",
    },
]
```

#### Ratings  
 
 To import tariff plans (rates, destination-rates, rating-plans and rating profiles) from a `JSON` file use `finance_import_tariffs` custom command.
 - `python manage.py finance_import_tariffs [file_path]`  
 - e.g. `python manage.py finance_import_tariffs /usr/share/dest.json`   
 
 This command uses one mandatory argument named `file_path`. `file_path` is the absolute path of `JSON` file that contains all tariff objects. This file must have `rates`, `destination_rates`, `rating_plans` and `rating_profiles` keys and follow conventions for each of them.

#### Branches

To import branches from a `JSON` file use `finance_import_branches` custom command.
 - `python manage.py finance_import_branches [file_path]`  
 - e.g. `python manage.py finance_import_branches /usr/share/dest.json`   
 
This command uses one mandatory argument named `file_path`. `file_path` is the absolute path of `JSON` file that contains all branch objects. This file must be structured like this:

```
[
    {
        "branch_code": "tehran",
        "branch_name": "Tehran",
        "destination_names": [
            "Tehran",
        ]
    },
]
```

#### Import credits

To import subscriptions' existing credits from an excel file use `finance_import_credits` custom command. This command take file path, subscription column name and credits column name as arguments.
- `python manage.py finance_import_credits [file_path] [subscription_code_column_name] [credit_column_name]`

E.g: `python manage.py finance_import_credits /home/user/credits.xlsx SubId  BillAmount`

#### Import runtime configs

Runtime configs handles corporate prefixes, invoice due date and other runtime related variables.

- `python manage.py finance_update_runtime_config`

## Jobs

`CGG` Uses three different jobs to handle issuing invoices, checking due dates of invoices, rerunning failed jobs and checking for loose channels. these are custom commands in django that should be cron jobbed to run daily. 

#### Setting up jobs

`CGG` custom command's must run in the same environment (database and `local.env`) of the running application. so the run each of these the first step is to activate the same virtual python of running `CGG`, then source the `local.env` and lastly run the command.

#### Running custom commands

To issue periodic invoices this command should run every day:  

- `python manage.py finance_periodic_invoice`    

To check due dates this command should run every day:  

- `python manage.py finance_due_date`    

To check due dates for service deallocation:  

- `python manage.py finance_deallocation`   

To redo failed jobs:  

- `python manage.py finance_failed_jobs`  

To check data integrity:  

- `python manage.py finance_integrity_check`  

To check for loose channels and disconnect them:  

- `python manage.py finance_check_loose_sessions`  
