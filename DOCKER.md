# Docker mode

1. Create `docker/configs/env` directory based on `docker/configs/env.example`
2. Change local variables located in `app.env`
3. Run (build and run) docker containers using `sudo docker-compose up [--build]`

## Installation

- `docker-compose exec cgg_app_1 docker/commands/install.sh`

## Update

- `docker-compose exec cgg_app_1 docker/commands/update.sh`

## Update tariffs only

- `docker-compose exec cgg_app_1 docker/commands/tariff.sh`

## Update destinations only

- `docker-compose exec cgg_app_1 docker/commands/destinations.sh`

## Jobs

`CGG` Uses five different jobs to handle issuing invoices, checking due dates of invoices, checking for data integrity, rerunning failed jobs and checking for loose channels. these are custom commands in django that should be cron jobbed to run daily or hourly and every five minutes. 

- `docker-compose exec cgg_app_1 docker/commands/daily.sh`
- `docker-compose exec cgg_app_1 docker/commands/hourly.sh`
- `docker-compose exec cgg_app_1 docker/commands/every-five-min.sh`

## Port

`CGG` docker mode uses `HAProxy` to load balance between two services of `CGG` app and exposes one port to the host. If you want to change this port you can modify the `cgg_ha` section of `docker-compose.yml` file.

- `http` on `8080` for APIs
- `http` on `8989` for `HAProxy` stats
