## RC - TBD

### Changed

- Round price with a deduction of one thousand rials and put the difference to debt field

### Issues

- `CGRAT-256`

## Version 1.7.0 - 13 October 2021

### Changed

- Change invoice calculation based on half minutes and minutes
- Change tariff.json

### Fixed

- Add missed destination rates for DR_Tehran

### Issues

- `CGRAT-254 CGRAT-255`

## Version 1.6.0 - 21 February 2021

### Added

- Add import destinations command to docker mode

### Issues

- `CGRAT-253`

## Version 1.5.1 - 21 February 2021

### Fixed

- Add missed mobile national prefixes

### Issues

- `CGRAT-252`

## Version 1.5.0 - 17 February 2021

### Added

- Verify and repair subscription's balance in admin panel

### Issues

- `CGRAT-251`

## Version 1.4.1 - 14 February 2021

### Fixed

- Fix the false alarms in objects check integrity

### Issues

- `CGRAT-250` 

## Version 1.4.0 - 27 January 2021

### Added

- Verify and repair mechanism for threshold invoices

### Fixed

- Fix the body of prepaid expiration message

### Issues

- `CGRAT-248 CGRAT-249`

## Version 1.3.2 - 24 January 2021

### Fixed

- Fix issuing multiple bypass mode invoices

### Issues

- `CGRAT-247`

## Version 1.3.1 - 12 January 2021

### Fixed

- Fix loading default packages
- Show all fields in list of packages

### Issues

- `CGRAT-246`

## Version 1.3.0 - 5 January 2021

### Added

- Add discount on packages

### Changed

- Add new fields to invoice API of SIAM
- Update and merge documents

### Issues

- `CGRAT-246 TB-193 DEV-14` 

## Version 1.2.1 - 22 December 2020

### Fixed

- Fix considering failed jobs as done after notifying trunk backend

### Issues

- `CGRAT-245`

## Version 1.2.0 - 13 December 2020

### Changed

- Issue interim invoices asynchronous to avoid timeouts

### Fixed

- Fix getting total count of query set in pagination

### Issues

- `CGRAT-243 CGRAT-244`

## Version 1.1.0 - 8 December 2020

### Added

- Add deallocation cause and blacklist deallocated numbers based on the cause
- Consider payment cool down on automatic invoice issuing
- Add safe delete invoices to django panel

### Changed

- Optimize runtime config usages 
- Calculate national number rates per seconds
- Change due date on periodic invoices to be the number of periods

### Fixed

-  Fix getting CDRs with negative cost from CGRateS

### Issues

- `CGRAT-237 CGRAT-238 CGRAT-239 CGRAT-240 CGRAT-241 CGRAT-242 DEV-22`

## Version 1.0.0 - 17 November 2020

### Added

- Add a command to clean log database
- Start logging database errors

### Changed

- Update all dependencies and codes related to updates
- Refactor all apps to achieve more decoupling
- Use `ENTRYPOINT` instead of `CMD` in `Dockerfile`
- Refactor API URLs to accept requests without the ending slash as well
- Start using `python` version `3.9`

### Fixed

- Disable the active package invoice after converting subscription to postpaid
- Fix cause of due date messages

### Issues

- `DEV-22 CGRAT-232 CGRAT-234`

## Version 0.11.1 - 22 October 2020

### Fixed 

- Make periodic invoice command timezone aware

### Issues

- `CGRAT-231`

## Version 0.11.0 - 12 October 2020

### Added
- Add cause to notification of interim invoices
- Add a custom command to update runtime configs
- Add a custom command to handle automatic service deallocation
- Add `deallocated_at` and `latest_paid_at` to subscriptions
- Add `deallocate_warned` to subscriptions

### Changed
- Change the behavior of postpaid max usage
- Refactor method names
- Refactor notify trunk related services
- Change the behavior of due date in invoices
- Refactor due date and deallocation commands to send warnings

### Removed
- `periodic_due_notified` and `periodic_due` from invoices

### Issues
- `CGRAT-226 CGRAT-227 CGRAT-228 CGRAT-229 CGRAT-230`

## Version 0.10.6 - 24 September 2020

### Fixed
- Fix calculating corporate usage and cost in invoices
- Fix filtering CDRs for issuing invoices and profits
- Prevent decreasing base balance of subscriptions' if used balance is greater than the new base balance


### Issues
- `CGRAT-223 CGRAT-224 CGRAT-225`


## Version 0.10.5 - 22 September 2020

### Fixed
- Increase connect time on post to trunk to prevent timeout on large data

### Issues
- `CGRAT-222`

## Version 0.10.4 - 22 September 2020

### Fixed
- Fix persisting Redis data on disk in docker mode 
- Consider revoking latest unpaid invoices in no pay mode 

### Issues
- `CGRAT-220 CGRAT-221`


## Version 0.10.3 - 20 September 2020

### Fixed
- Separate daily and hourly jobs in docker mode

### Issues
- `CGRAT-219`


## Version 0.10.2 - 13 September 2020

### Fixed
- Fix setting due date of invoices
- Fix some translations on invoices

### Issues
- `CGRAT-217`


## Version 0.10.1 - 12 September 2020

### Fixed
- Add subscription code and number to export credit invoices
- Make exported dates timezone aware 
- Fix generic or on customer code's value
- Force change some RuntimeConfigs to integer

### Issues
- `CGRAT-216`


## Version 0.10.0 - 10 September 2020

### Added
- Add the ability to bypass pagination
- Add new filters to subscriptions and payments
- Add filter on operation type to credit invoice
- Add the ability to decrease base balances
- Add friendly filter to credit invoices
- Add payment cool down option
- Add package name and code to package invoices data
- Add credit to customer's serializer
- Add health check urls
- Add an API to handle a large number of filters on subscriptions
- Handle auto pay notification for interim/periodic invoices
- Use celery jobs to handle CGRateS notifications

### Changed
- Add prime code to all invoices and payments
- Update tariff plans default json file based on the new tariffs
- Set thresholds with maximum rate fee instead of minimum (ignore international)
- Improve the performance of caching system
- Improve the performance of CSV exporter
- Add new filters to payment and change it's serializer
- Improve issuing periodic invoices

### Fixed
- Fix notification API URLs on trunk backend
- Remove all thresholds on a subscription on delete process
- Fix non distinct results when using generic or filter
- Fix generating duplicate package code after deleting one
- Fix redoing failed jobs
- Fix generic or on customer codes greater than 10
- Fix decreasing base balance when current balance is smaller than the new base
- Fix removing prepaid base balance on convert process

### Issues
- `TB-135 TB-136 TB-140 TB-145 CGRAT-197 CGRAT-198 CGRAT-199 CGRAT-200 CGRAT-201 CGRAT-202 CGRAT-203 CGRAT-204 CGRAT-205 CGRAT-206 CGRAT-207 CGRAT-208 CGRAT-210 TB-153 CGRAT-210 CGRAT-213 CGRAT-214 TB-159`

## Version 0.9.0 - 09 August 2020

### Changed
- Add one day due date to package invoices

### Fixed
- Fix filter by subscription type in subscriptions API
- Fix exporting of invoices (introduced after fixing pagination)
- Fix payment filter on created at range
- Fix time format in creating action plans

### Issues
- `CGRAT-192 CGRAT-193 CGRAT-194 CGRAT-195 CGRAT-196`

## Version 0.8.0 - 28 July 2020

### Added
- Auto generate package code if it's empty
- Add `Generic OR` filter for all resources (`invoice`/`base-balance-invoice`/`credit-invoice`/`package-invoice`/`payment`)

### Changed
- Create subscription now accepts any package to initialize prepaid subscription

### Fixed
- Fix converting date time received from CGRateS

### Issues
- `CGRAT-189 CGRAT-190 CGRAT-191`


## Version 0.7.0 - 4 July 2020

### Added
- Add new APIs to handle increasing base balance and credit without payment
- Add a new API to increase the current balance of a subscription without payment
- Add auto pay mode for invoices
- Add periodic invoices for prepaid subscriptions as well

### Changed
- Change payment and all invoices APIs to accept customer code without subscription code as well
- Change sending notification to trunk
- Refactor subscription service to be more DRY
- Use credit in customer instead of subscription

### Fixed
- Fix force debiting postpaid balance
- Fix default ordering on package, destination and runtime configs
- Return paid at in list of all invoices

### Issues
- `CGRAT-181 CGRAT-182 CGRAT-183 CGRAT-184 CGRAT-185 CGRAT-186 TB-102 TB-112`

##  Version 0.6.1 - 13 June 2020

### Fixed 
- Add emergency numbers for every landline national

### Issues
- `CGRAT-178`


## Version 0.6.0 - 10 June 2020

### Added
- Handle ratings for emergency numbers

### Changed 
- Add inbound and outbound usage to profits
- Add total usage and cost to profits
- Separate divide on percent for inbound and outbound calls of operators
- Update python version to the latest stable version of `3.8`
- Protect data instead of cascade on delete
- Accept two formats of dates from CGRateS in CDRs

### Fixed
- Fix unauthorized error responses schema
- Fix invoice migration from RSPSRV
- Fix price and value for default package
- Fix force reloading cache on base balances
- Fix calculating expired value of package invoices (introduced in this version)

### Issues
- `TB-81 TB-85 TB-87 CGRAT-176 CGRAT-177 CGRAT-178 CGRAT-179 CGRAT-180`

## Version 0.5.0 - 30 May 2020
 
### Added
- Add filter on total cost for invoices
- Add expired at to package invoices
- Add activation for packages
- Add featured packages
- Add start and end date for packages
- Add on demand interim invoice for both customers and admin
- Get invoices/base-balance-invoices/package-invoices' related payments
- Add status code to profits
- Add a new API to update profit's status code
- Detect frauds in creating interim invoices to bypass due date
- Add a new key to runtime configs to handle periodic due dates
- Add a new API to get and update runtime configs
- Add two new attributes to invoices to handle periodic overdue
- Add new APIs to export payments, package invoices, invoices, credit invoices and base balance invoices as CSV

### Changed
- Persist total cost of invoices in database
- Change filter query of profits to support status code
- Change daily commands in docker mode
- Handle periodic due dates in due date custom command

### Removed
- Remove expiration date from package invoices 

### Issues
- `CGRAT-166 CGRAT-167 CGRAT-168 CGRAT-169 CGRAT-170 CGRAT-171 CGRAT-172 CGRAT-173 CGRAT-174`


## Version 0.4.0 - 14 May 2020

### Added
- Maintain data integrity for all models in finance app
- Convert prepaid subscriptions to postpaid

### Changed
- Make more models readonly in admin panel
- Handle CGRateS timeout once (Recovery mode)
- Add caching objects and force delete caches
- Improve docker mode for redis and compiled messages
- Separate log database from main application

### Fixed
- Fix Creating unlimited subscriptions
- Fix creating corporate numbers based on branches
- Fix persisting redis data in docker mode
- Fix preventing default branches
- Fix casting numbers in credit update (No pay mode)

### Issues
- `CGRAT-152 CGRAT-153 CGRAT-154 CGRAT-155 CGRAT-156 CGRAT-157 CGRAT-158 CGRAT-159 CGRAT-160 CGRAT-161 CGRAT-162 CGRAT-163` 
    
## Version 0.3.1 - 30 Apr 2020

### Added
- Add docker mode

### Changed
- Optimize database indexes
- Upgrade `python` version to `3.8.2`

### Issues
- `CGRAT-148 CGRAT-149` 

## Version 0.3.0 - 25 Apr 2020

### Added
- Add prepaid package flow
- Add new subscription type. Now subscription types are `prepaid`, `postpaid`, `unlimited`

### Removed
- Subscription type is not compatible with previous versions

### Issues
- `CGRAT-143 CGRAT-145 CGRAT-146 DEV-14 DEV-22` 
    
## Version 0.2.2 - 20 Apr 2020

### Added
- Add electronic wallet (Credit)
- Add discount to invoices
- Add hybrid payment flow
- Add offline payment flow
- Add `ASGI` support

### Changed
- Improve code styles on filtering queries
- Change packaging based on package name conventions

### Removed
- Payments for invoices and base balance invoices

### Fixed
- Add missed usage of corporate costs in issuing invoices (Tax and Credit) 
- Fix revert account name with tenant
- Fix returning 404 error for basic app's destinations

### Removed
- Dynamic days to issue periodic invoices

### Issues
- `DEV-22 CGRAT-132 CGRAT-51 CGRAT-133 CGRAT-134 CGRAT-135 CGRAT-136 CGRAT-137 CGRAT-140 CGRAT-141`
     
## Version 0.2.1 - 27 Feb 2020

### Added
- Add independent rating plan for country corporate numbers 
- Introduce subscriptions' type (Limited/Unlimited)
- Add a new custom command to renew all subscriptions' type
- Introduce new functionality to remove thresholds
- Add a new API to remove subscriptions (Use with cautious)
- Add corporate rates to invoices

### Changed
- Upgrade `python` version to `3.8.1`
- Start using `Django` version `3.0.3`
- Refactor base service method names
- Minor code style improvements
- Polish `.gitignore`
- Reformat tariffs and use rate and `rate_increment` instead of `connect_fee`
- Change the schema of `CGRateS` rate's table to support bigger numbers
- Improve the UX of django admin panel

### Fixed
- Prevent deleting `RuntimeConfigs`
- Fix custom command import branch logger name
- Translate missing messages
- Consider subscription fee only on periodic invoices
- Consider ignoring corporate numbers in invoice calculation (for generic landlines)
- Consider not destination prefixes in issuing invoices to avoid processing duplicate CDRs
 
### Deprecated
- Dynamic days to issue periodic invoices
    
## Version 0.2.0 - 15 Feb 2020

### Added
- Add support for `CGRateS v0.10.0`
- Add basic authentication for requests from Gateway to `CGRateS`
- Issue an interim invoice on 100 percent usage
- Import subscriptions' credit
- Migrate invoices and base balance invoices from `RSPSRV`

### Changed
- Consider subscription fee in invoices (from `MIS`)
- Consider free ratings for calls from Respina users to each other

### Fixed
- Fix messages and translations
- Fix updating subscriptions' availability after successful pay

## Version 0.1.2 - 12 Feb 2020

### Added
- Add a custom command to initialize `CGRateS`

### Changed
- Refactor phone numbers based on `E.164` format

### Fixed
- Fix `CGRateS` priority weight
- Fix rounding decimals in profits
- Fix creating attribute profiles for operators
- Fix using minimum rates for 80 an 100 percent usage
- Fix normalizing numbers to only match numbers
    
## Version 0.1.1 - 22 Jan 2020

### Added
- Add translation for error messages
- Introduce new `API` to get destinations based on names

### Changed
- Improve performance by eliminating some `API` calls:
    - Change the creation process of attribute profiles
    - Change the creation process of thresholds
    - Refactor load tariffs from `json`
- Refactor local environment (remove trunk relative urls)
- Refactor branch `APIs` to manage tariffs directly
- Consider minimum rate of branches in max usage thresholds
    
### Fixed
- Minor bug fixes in profits and operators
- Minor improvements in `django` admin panel
- Minor bug fixes on branch `APIs`
    
## Version 0.1.0 - 12 Jan 2020

### Added
- Compatible with `CGRateS v0.9.1rc`
- Manage operators, branches, profits
- Manage destinations, rates and tariff plans
- Use database caching to cache `API` responses
- Log all `API` requests
- Handle web hook calls from `CGRateS`
- Connected to `RSPSRV` project 
- Manage customers and subscriptions:
    - Manage invoices and base-balance-invoices
    - Manage payments