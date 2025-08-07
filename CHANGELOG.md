# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/). See [standard-version](https://github.com/conventional-changelog/standard-version) for commit guidelines.

## v1.1.0 (2025-08-07)

### Feat

- add support for new `fandom` path in some ososedki crawlers (#195)
- add support for `cosplay` in ososedki main site, still no support for models
- add missing site paths on some ososedki-based crawlers (#193)
- add support for pagination in ososedki sites
- add retries limit to the processing of the album
- **cli**: add new optional argument `cache` for request caching support
- **cli**: add list-supported-sites argument
- add crawler for cosxuxi.club (#181)
- enhance and simplify error printing at the end

### Fix

- always import needed info from bs4, refactor functions to avoid passing session as argument, add more type hints
- **crawlers**: handle possible errors when fetching paginated content
- **crawlers**: restore bunkr-albums functionality
- **crawlers**: add missing pagination attribute in BaseCrawler class
- **logs**: setup global logger with new core-helpers implementation
- **fapello_is**: update api fetch url, set referer in requests headers
- set the user-agent globally to be reused during all the session
- replace non-working vhs-action with full vhs installation using go, simplify gif commit
- ensure creation of program folders on 1st run
- **download**: process the retried response properly in case of error
- **eromexxx**: fix typo in User Agent used in the requests

### Refactor

- flatten the downloading chunk results in a way more idiomatic
- **crawlers**: move common crawler functionality into base abstract class, make ososedki base crawler inherit from that class
- **crawlers**: remove no longer needed CrawlerContext type import
- **crawlers**: simplify some crawlers reusing context session instead of new session
- set context as crawler class attribute to allow easy access to context information
- lazily evaluate type hints, avoid import type hints libraries during runtime
- convert all crawlers into classes with inheritance

## v1.0.1 (2025-01-12)

### Fix

- **cli**: remove default False value for argument print-config

## v1.0.0 (2025-01-12)

### Feat

- add support for user options arguments
- add vipthots crawler
- add ocosplay crawler
- add cosplaythots crawler
- **scrappers**: add support for cosplay fetching and downloading for ososedki common sites (cosplayasian, cosplayboobs, cosplayrule34 and waifubitches)
- **eromexxx**: use only highest_offset for album downloading
- configure paths on program start
- create config module to store download path, add new cli args:
- add cosplayboobs crawler
- add cosplayasian crawler
- add cosplayrule34 crawler
- **waifubitches**: add support for model page scrapping
- add waifubitches crawler
- remove downloaders list, dynamically load crawlers modules
- **husvjjal_blogspot**: add support for extraction of related albums
- **utils**: change fetch functions to accept any session request parameter (headers, params, data, etc.)
- **husvjjal_blogspot**: add entry in downloaders
- **husvjjal_blogspot**: add support for video downloading
- add base crawler for husvjjal, pending to retrieve videos and related albums
- add crawler for bunkrr_albums
- **utils**: modify get_valid_url() to accept multiple URLs
- simplify the scrapping module, remove individual scrapper function
- **utils**: improve filename preparing to retrieve realistic name
- **utils**: add headers to retrieve full sorrymother videos
- **utils**: add more error control on file writing
- **fapello_is**: add more output information on scrapping

### Fix

- handle 503 and SSL error responses, keep same user agent all over the session
- **scrapper**: validate download URL before scrapping
- **waifubitches**: remove exception raising
- **utils**: remove max timeout for aiohttp.
- **husvjjal_blogspot**: enhance URL sanitization with urlparse to improve security (fixes #21)
- add missing const for the requests timeout
- add requests timeout according to bandit audit report
- add filename extension if it is not set
- remove invalid downloaders in current project state
- remove misleading and useless loop
- **ososedki**: add more error control on title extraction
- **utils**: move fetching exception handling for proper results
- **utils**: update filename retrieval from url to be more robust
- replace hashing function for security purposes
- remove old misleading code
- add missing __init__ package file

### Refactor

- separate the downloading functionality into a separate module
- simplify common scrappers (cosplayasian, cosplayboobs, cosplayrule34 and waifubitches) to handle same download functionality
- adapt consts module to use core_helpers utilities
- simplify functions with core_helpers, add welcome print
- group common code from ososedki and waifubitches
