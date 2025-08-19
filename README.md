<p align="center">
    <img width="350" src="https://i.imgur.com/BRi2FsF.png" alt="Ososedki-dl logo">
</p>

<p align="center">
    <a href="https://github.com/YisusChrist/ososedki_dl/issues">
        <img src="https://img.shields.io/github/issues/YisusChrist/ososedki_dl?color=171b20&label=Issues%20%20&logo=gnubash&labelColor=e05f65&logoColor=ffffff">&nbsp;&nbsp;&nbsp;
    </a>
    <a href="https://github.com/YisusChrist/ososedki_dl/forks">
        <img src="https://img.shields.io/github/forks/YisusChrist/ososedki_dl?color=171b20&label=Forks%20%20&logo=git&labelColor=f1cf8a&logoColor=ffffff">&nbsp;&nbsp;&nbsp;
    </a>
    <a href="https://github.com/YisusChrist/ososedki_dl/stargazers">
        <img src="https://img.shields.io/github/stars/YisusChrist/ososedki_dl?color=171b20&label=Stargazers&logo=octicon-star&labelColor=70a5eb">&nbsp;&nbsp;&nbsp;
    </a>
    <a href="https://github.com/YisusChrist/ososedki_dl/actions">
        <img alt="Tests Passing" src="https://github.com/YisusChrist/ososedki_dl/actions/workflows/github-code-scanning/codeql/badge.svg">&nbsp;&nbsp;&nbsp;
    </a>
    <a href="https://github.com/YisusChrist/ososedki_dl/pulls">
        <img alt="GitHub pull requests" src="https://img.shields.io/github/issues-pr/YisusChrist/ososedki_dl?color=0088ff">&nbsp;&nbsp;&nbsp;
    </a>
    <a href="https://deepwiki.com/YisusChrist/ososedki_dl">
        <img src="https://deepwiki.com/badge.svg" alt="Ask DeepWiki">&nbsp;&nbsp;&nbsp;
    </a>
    <a href="https://opensource.org/license/GPL-3.0/">
        <img alt="License" src="https://img.shields.io/github/license/YisusChrist/ososedki_dl?color=0088ff">
    </a>
</p>

<br>

<p align="center">
    <a href="https://github.com/YisusChrist/ososedki_dl/issues/new?assignees=YisusChrist&labels=bug&projects=&template=bug_report.yml">Report Bug</a>
    ·
    <a href="https://github.com/YisusChrist/ososedki_dl/issues/new?assignees=YisusChrist&labels=feature&projects=&template=feature_request.yml">Request Feature</a>
    ·
    <a href="https://github.com/YisusChrist/ososedki_dl/issues/new?assignees=YisusChrist&labels=question&projects=&template=question.yml">Ask Question</a>
    ·
    <a href="https://github.com/YisusChrist/ososedki_dl/security/policy#reporting-a-vulnerability">Report security bug</a>
</p>

<br>

![Alt](https://repobeats.axiom.co/api/embed/d776dfb3239e733c3333eb2cf4f8924bd6478660.svg "Repobeats analytics image")

<br>

`ososedki_dl` is a Python app that allows you to download all the images from online albums. The program is designed to be simple and easy to use, with a command-line interface that allows you to download images from the website with a single command. Check the [Supported sites](#supported-sites) section to see the list of supported websites.

<details>
<summary>Table of Contents</summary>

- [Requirements](#requirements)
- [Installation](#installation)
  - [From PyPI](#from-pypi)
  - [Manual installation](#manual-installation)
  - [Uninstall](#uninstall)
- [Usage](#usage)
  - [Example of execution](#example-of-execution)
  - [Progress bars](#progress-bars)
  - [Supported sites](#supported-sites)
- [Contributors](#contributors)
  - [How do I contribute to ososedki\_dl?](#how-do-i-contribute-to-ososedki_dl)
- [License](#license)
- [Credits](#credits)

</details>

## Requirements

Here's a breakdown of the packages needed and their versions:

- [poetry](https://pypi.org/project/poetry) >= 1.7.1 (_only for manual installation_)
- [aiofiles](https://pypi.org/project/aiofiles) >= 24.1.0
- [aiohttp](https://pypi.org/project/aiohttp) >= 3.9.5
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4) >= 4.12.2
- [fake-useragent](https://pypi.org/project/fake-useragent) >= 1.5.1
- [platformdirs](https://pypi.org/project/platformdirs) >= 4.2.2
- [requests](https://pypi.org/project/requests) >= 2.31.0
- [requests-pprint](https://pypi.org/project/requests-pprint) >= 1.0.1
- [rich](https://pypi.org/project/rich) >= 13.5.3
- [tldextract](https://pypi.org/project/tldextract) >= 5.1.2
- [validators](https://pypi.org/project/validators) >= 0.22.0

> [!NOTE]
> The software has been developed and tested using Python `3.12.1`. The minimum required version to run the software is Python 3.9. Although the software may work with previous versions, it is not guaranteed.

## Installation

### From PyPI

`ososedki_dl` can be installed easily as a PyPI package. Just run the following command:

```bash
pip3 install ososedki_dl
```

> [!IMPORTANT]
> For best practices and to avoid potential conflicts with your global Python environment, it is strongly recommended to install this program within a virtual environment. Avoid using the --user option for global installations. We highly recommend using [pipx](https://pypi.org/project/pipx) for a safe and isolated installation experience. Therefore, the appropriate command to install `ososedki_dl` would be:
>
> ```bash
> pipx install ososedki_dl
> ```

The program can now be ran from a terminal with the `ososedki_dl` command.

### Manual installation

If you prefer to install the program manually, follow these steps:

> [!WARNING]
> This will install the version from the latest commit, not the latest release.

1. Download the latest version of [ososedki_dl](https://github.com/YisusChrist/ososedki_dl) from this repository:

   ```bash
   git clone https://github.com/YisusChrist/ososedki_dl
   cd ososedki_dl
   ```

2. Install the package:

   ```bash
   poetry install --only main
   ```

3. Run the program:

   ```bash
   poetry run ososedki_dl
   ```

### Uninstall

If you installed it from PyPI, you can use the following command:

```bash
pipx uninstall ososedki_dl
```

## Usage

> [!TIP]
> For more information about the usage of the program, run `ososedki_dl --help` or `ososedki_dl -h`.

![Usage](demo.gif)

The program can be run from the terminal with the `ososedki_dl` command. It will ask you to introduce the URL of the album you want to download. The program will automatically detect the domain, scrape the media (images and videos) and download them to the path specified by the user.

### Example of execution

https://github.com/user-attachments/assets/1b82d20f-1680-4cda-9021-ebd0f87a72ed

### Progress bars

Since 2025-08-18, the program includes progress bars for downloading processes. This feature provides a visual indication of the progress of the operations, making it easier to track the status of the downloads. There are two types of progress bars:

- **Albums**: This bar shows the progress of the whole downloading process, indicating how many items have been downloaded from the album. In case you are downloading a profile, it will display as many bars as albums in the profile, each showing the progress of the respective album. Example:

  https://github.com/user-attachments/assets/691e10c8-4256-4ce1-be88-7684b3798765

- **Videos**: This bar shows the progress of a single video being downloaded. It indicates how much of the video has been downloaded so far.

  https://github.com/user-attachments/assets/8bdc1de9-32eb-4cc2-96ae-061e1df76e1c

### Supported sites

| Domain              | URL                           | Scrapping          | Downloading        |
| ------------------- | ----------------------------- | ------------------ | ------------------ |
| `eromexxx`          | https://eromexxx.com          | :heavy_check_mark: | :heavy_check_mark: |
| `fapello_is`        | https://fapello.is            | :heavy_check_mark: | :heavy_check_mark: |
| `ososedki`          | https://ososedki.com          | :heavy_check_mark: | :heavy_check_mark: |
| `sorrymother`       | https://sorrymother.to        | :heavy_check_mark: | :heavy_check_mark: |
| `wildskirts`        | https://wildskirts.com        | :heavy_check_mark: | :heavy_check_mark: |
| `bunkr-albums`      | https://bunkr-albums.io       | :heavy_check_mark: | :x:\*              |
| `husvjjal_blogspot` | https://husvjjal.blogspot.com | :heavy_check_mark: | :heavy_check_mark: |
| `waifubitches`      | https://waifubitches.com      | :heavy_check_mark: | :heavy_check_mark: |
| `cosplayasian`      | https://cosplayasian.com      | :heavy_check_mark: | :heavy_check_mark: |
| `cosplayrule34`     | https://cosplayrule34.com     | :heavy_check_mark: | :heavy_check_mark: |
| `cosplayboobs`      | https://cosplayboobs.com      | :heavy_check_mark: | :heavy_check_mark: |
| `cosplaythots`      | https://cosplaythots.com      | :heavy_check_mark: | :heavy_check_mark: |
| `ocosplay`          | https://ocosplay.com          | :heavy_check_mark: | :heavy_check_mark: |
| `vipthots`          | https://vipthots.com          | :heavy_check_mark: | :heavy_check_mark: |
| `cosxuxi`           | https://cosxuxi.club          | :heavy_check_mark: | :heavy_check_mark: |

**\*** _The program will only scrape the media and display the URLs. You can easily pass all the URLs to the great [CyberDropDownloader](https://github.com/Jules-WinnfieldX/CyberDropDownloader) and download all of them with one command_:

```sh
cyberdrop_dl <URL1> <URL2> <URL3> ...
```

## Contributors

<a href="https://github.com/YisusChrist/ososedki_dl/graphs/contributors"><img src="https://contrib.rocks/image?repo=YisusChrist/ososedki_dl" /></a>

### How do I contribute to ososedki_dl?

Before you participate in our delightful community, please read the [code of conduct](https://github.com/YisusChrist/.github/blob/main/CODE_OF_CONDUCT.md).

I'm far from being an expert and suspect there are many ways to improve – if you have ideas on how to make the configuration easier to maintain (and faster), don't hesitate to fork and send pull requests!

We also need people to test out pull requests. So take a look through [the open issues](https://github.com/YisusChrist/ososedki_dl/issues) and help where you can.

See [Contributing Guidelines](https://github.com/YisusChrist/.github/blob/main/CONTRIBUTING.md) for more details.

## License

`ososedki_dl` is released under the [GPL-3.0 License](https://opensource.org/license/GPL-3.0).

## Credits

![preview](https://opengraph.githubassets.com/963eaba4b5ff0640d87891ec7989d89d70dba767722bdf84d19aa46bda3a933b/Jules-WinnfieldX/CyberDropDownloader)

This program is heavily inspired by [Jules-WinnfieldX](https://github.com/Jules-WinnfieldX)'s [CyberDropDownloader](https://github.com/Jules-WinnfieldX/CyberDropDownloader). Sadly, the project is no longer maintained; hence, the creation of this project to try to bring support for more websites and improve the codebase.
