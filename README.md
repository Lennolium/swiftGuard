<!--- Logo -->

<div align="center">  
<picture>
  <source media="(prefers-color-scheme: dark)" srcset="./img/banner/banner_dark.png" width="600vw">
  <source media="(prefers-color-scheme: light)" srcset="./img/banner/banner_light.png" width="600vw">
  <img alt="Application Banner" src="./img/banner/banner_light.png" width="600vw">
</picture>
</div>
<br>

<!--- Badges -->

<div align="center"> 
  <a href="https://github.com/Lennolium/swiftGuard/branches" > 
    <img src="https://img.shields.io/github/last-commit/Lennolium/swiftGuard?label=Last%20Updated&color=orange" alt="last updated" >
  <a></a>  
   <a href="https://app.codacy.com/gh/Lennolium/swiftGuard/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade" > 
    <img src="https://app.codacy.com/project/badge/Grade/7e4271efc8894c9fab80e2f27f896a87" alt="code quality" >
    <a></a>
   <a href="https://github.com/Lennolium/swiftGuard/commits/master" > 
    <img src="https://img.shields.io/github/commit-activity/m/Lennolium/swiftGuard?label=Commit%20Activity" 
alt="commit activity" >
     <a></a>
  <a href="https://github.com/Lennolium/swiftGuard#download" > 
    <img src="https://img.shields.io/badge/Version-0.0.1-brightgreen" 
alt="stable version" >
     <br>
  <a href="https://github.com/Lennolium/swiftGuard/issues" > 
    <img src="https://img.shields.io/github/issues-raw/Lennolium/swiftGuard?label=Open%20Issues&color=critical" alt="open issues" >
  <a href="https://github.com/Lennolium/swiftGuard/issues?q=is%3Aissue+is%3Aclosed" > 
    <img src="https://img.shields.io/github/issues-closed-raw/Lennolium/swiftGuard?label=Closed%20Issues&color=inactive" alt="closed issues" > 
     <a href="#" > 
    <img src="https://img.shields.io/github/repo-size/Lennolium/swiftGuard?label=Repo%20Size&color=yellow" alt="repo size" >
  <a href="https://github.com/Lennolium/swiftGuard/blob/main/LICENSE" > 
    <img src="https://img.shields.io/github/license/Lennolium/swiftGuard?label=License&color=blueviolet" alt="License" > 
  <a></a> </a> </a> </a> </a> </a> </a> </a> </a>
</div>

<!--- Title -->

<div align="center">
  <h1></h1> 
</div>

<!--- Description -->



<div align="center">
Anti-forensic macOS tray application designed to safeguard your system by monitoring USB ports. 
It ensures your device's security by automatically initiating either a system shutdown or hibernation 
if an unauthorized device connects or a connected device is unplugged. It offers the flexibility to whitelist 
designated devices, to select an action to be executed and to set a countdown timer, allowing to disarm the 
shutdown process.
<br><br>

[![Donate](https://img.shields.io/badge/Donate-Paypal-blue?style=flat-square&logo=paypal)](https://www.paypal.me/smogg)
[![BuyMeACoffee](https://img.shields.io/badge/Buy%20me%20a-Coffee-f5d132?style=flat-square&logo=buymeacoffee)](https://buymeacoffee.com/lennolium)
</div>
<div align="center">
  <h3></h3>  
    </div>     
&nbsp;

<!--- Table of contents -->

## Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Why should you care?](#why-should-you-care)
- [Installation](#installation)
- [Usage](#usage)
    - [GUI](#gui)
    - [CLI](#cli)
- [Development](#development)
- [Roadmap](#roadmap)
- [Credits](#credits)
- [License](#license)

&nbsp;

<!--- Features -->

## Features

- __Monitoring:__ Continuously monitors USB ports for device activity, even in sleep mode.
- __Whitelisting:__ Allows users to whitelist authorized devices, ensuring 
  hassle-free connectivity.
- __Discrete:__ Operates in the macOS system tray, minimizing 
  interruptions.
- __Customizable:__ Allows users to configure various settings, including 
  action (shutdown/hibernate), countdown timer and whitelist.
- __Lightweight:__ Designed to consume minimal system resources for optimal 
   performance.
- __Privacy:__ Does not require an internet connection, ensuring the privacy 
   of your data.
- __Open Source:__ Provides transparency and 
  allows community contributions for continuous development.

&nbsp;

<!--- Screenshots -->

## Screenshots

<div align="center">  
<picture>
  <source srcset="./img/screenshots/screenshots.png" width="600vw">
  <img alt="Application Screenshots" src="./img/screenshots/screenshots.png" width="600vw">
</picture>
  
*__Left:__ Manipulation button to defuse the alarm. __Right:__ Whitelist and Settings menu.*
</div>
<br>

&nbsp;

<!--- Why -->

## Why should you care?

A few reasons to use this tool:

- __Anti-Forensic Measures:__ In case the police or other thugs break in. The police often use a [mouse jiggler](https://en.wikipedia.org/wiki/Mouse_jiggler)
to prevent the screen saver or sleep mode from being activated.
- __Prevent Data Exfiltration:__ You do not want someone adding or copying documents to or from your computer via USB.
- __Public Environments:__ If you frequently use your Mac in public places like libraries or cafes, swiftGuard 
acts as an additional layer of security against physical attacks in a [potentially vulnerable](https://www.ccn.com/fbi-illegally-stole-ross-ulbrichts-laptop-brought-silk-road/) setting.
- __Server Protection:__ You want to improve the security of your home or company server (e.g. your Raspberry Pi, NAS, etc.).
- __Data Protection Regulations:__ Many industries and organizations are subject to strict data protection 
regulations. swiftGuard helps maintain compliance by preventing unauthorized data transfers and access through USB ports.

> **Tip**: You might also want to use a cord to attach a USB key to your wrist. Then plug the key into your computer and 
> run swiftGuard. If your computer is robbed, the USB is removed and the computer shuts down immediately.

&nbsp;

<!--- Installation -->

## Installation

1. Obtain the most recent version by downloading it from [Releases](https://github.com/Lennolium/swiftGuard/releases).
2. Open the downloaded `swiftGuard.dmg` file.
3. Drag the swiftGuard application into the Applications folder.
4. Grant necessary permissions by opening `System Preferences > Security & Privacy > Privacy > Automation` and adding swiftGuard to 
   the list of applications.
5. For startup at login, open `System Preferences > General > Login Items` and add swiftGuard to the list of applications.
6. Open the swiftGuard application from the Applications folder.
7. swiftGuard should now appear in the macOS system tray.
8. Test at least once if the shutdown or hibernation is executed correctly. On first run you will be asked to grant the necessary
permissions by macOS.

&nbsp;
> **Important**: Make sure you use FileVault, macOS's built-in disk encryption feature, encrypt your entire disk, 
> ensuring that your data remains secure even if your device falls into the wrong hands. 
> Otherwise, unauthorized users may gain access to your data easily: `System Preferences > Security & Privacy > Security > FileVault` > Do NOT enable iCloud Recovery!

>__Note:__ If you get a warning that the application is from an _unidentified developer_, you have to open
>`System Preferences > Security & Privacy > Security` and click `Open Anyway`
>to allow the application to run. Alternatively, you can right-click on the application icon and select `Open`.

&nbsp;

<!--- Usage -->

## Usage

### GUI

1. Open the swiftGuard application from the Applications folder.
2. Click on the application icon in the macOS system tray to open the 
   main menu.
3. Click the `Guarding/Inactive` entry to start or pause the guarding of your USB ports.
4. The `Devices` menu displays all allowed and connected devices. Allowed devices are indicated with a checkmark, 
even if they are not connected.
5. To add or remove a device from the whitelist, simply click on the corresponding device entry.
6. If manipulation is detected, an alert (`Manipulation`) will appear in the main menu. Clicking on it 
will reset the alarm. The `Exit` button will not work.
7. In the `Settings` menu you can set a delay (0 - 60 seconds) and an action (`Shutdown` or `Hibernate`). The delay
determines how long swiftGuard will wait for you to reset/defuse the alarm before executing the action.
          
&nbsp;  

>**Notes:** 
>- swiftGuard alerts you if devices are removed that were connected before or while the application was started,
>except you add them to the whitelist. 
>- Connecting new devices will always trigger an alert, if these devices are not whitelisted.
>- If you encounter any problems, please check the log file in the `~/Library/Logs/swiftGuard` folder.
>- Your settings and whitelisted devices are stored in the `~/Library/Preferences/swiftGuard/swiftguard.ini` file.


&nbsp;

### CLI

You can run swiftGuard as a simple Python script from the command line without a graphical user interface (GUI). 
This is useful when operating swiftGuard on a headless system or saving system resources. However, you will lose the 
ability to defuse the shutdown process via the GUI, but you can kill the swiftGuard process from the command line 
instead. The preferences and whitelists are stored in the same location as the GUI version and can be edited 
manually. For further information, please refer to the [worker.py](https://github.com/Lennolium/swiftGuard/blob/main/src/swiftguard/worker.py) 
file located in the `/src/swiftguard` directory.


1. Open a terminal and navigate to the desired directory.
    ```bash
    cd ~/Desktop
    ```

2. Clone the repository.
    ```bash
    git clone https://github.com/Lennolium/swiftGuard.git
    ```

3. Navigate to the swiftGuard directory.
    ```bash
    cd swiftGuard
    ```

4. Install the [requirements](https://github.com/Lennolium/swiftGuard/blob/main/requirements.txt) in a new virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
    ```
   
5. Navigate to the src directory.
    ```bash
    cd src/swiftguard
    ```

6. Run the worker.py.
    ```bash
    python3 worker.py
    ```
&nbsp;

>**Notes:**
>- Settings/Whitelist: `~/Library/Preferences/swiftGuard/swiftguard.ini`
>- Logs: `~/Library/Logs/swiftGuard/swiftguard.log`
   
&nbsp;

<!--- Development -->

## Development

As an open-source project, I strive for transparency and collaboration in my development process. I greatly 
appreciate any contributions members of our community can provide. Whether you are fixing bugs, proposing features, 
improving documentation, or spreading awareness - your involvement strengthens the project. Please review the 
[code of conduct](https://github.com/Lennolium/swiftGuard/blob/main/.github/CODE_OF_CONDUCT.md) to understand how we work together 
respectfully.

- __Bug Report:__ If you are experiencing an issue while using the application, please [create an issue](https://github.com/Lennolium/swiftGuard/issues/new/choose).
- __Feature Request:__ Make this project better by [submitting a feature request](https://github.com/Lennolium/swiftGuard/discussions/2).
- __Documentation:__ Improve our documentation by [adding a wiki page](https://github.com/Lennolium/swiftGuard/wiki).
- __Community Support:__ Help others on [GitHub Discussions](https://github.com/Lennolium/swiftGuard/discussions).
- __Security Report:__ Report critical security issues via our [template](https://github.com/Lennolium/swiftGuard/blob/main/.github/SECURITY.md).

&nbsp;

<!--- Roadmap -->

## Roadmap

| **Now**                   | **Next**                                             | **Later**               |
|---------------------------|------------------------------------------------------|-------------------------|
| Unit tests                | Linux support                                        | CI/CD                   |
| Code quality              | Bluetooth detection                                  | Website/Docs/Wiki       |
| Translations              | Auto update                                          | Encrypted configuration |
| Package for Apple silicon | Auto start                                           | Code sign (Apple)       |
| Security audit            | More actions (wipe ram, delete files/folders, email) | User defined actions    |

&nbsp;

<!--- Security -->

## Security & Code Quality
Regarding swiftGuard is a security application and therefore security is of the utmost importance. I am committed to ensuring
that it is secure and reliable for all users. I am grateful for any feedback regarding security issues and will do my best to 
address them as quickly as possible. Please refer to the [security policy](https://github.com/Lennolium/swiftGuard/blob/main/.github/SECURITY.md) for more information.

Additionally, I let my code be checked by several code quality and security tools (Bandit, Black, Codacy, CodeQL, PMD CPD, Prospector, Pylint, Pysa, Pyre, Trivy, Radon). 
The results can be found by clicking on the badges below. These routines are no replacement for a manual code and security audit, but they help to find errors and vulnerabilities.
Please note that the results of these tools are not always accurate and may contain false positives.

<div align="center"> 
  <a href="https://app.codacy.com/gh/Lennolium/swiftGuard/dashboard?utm_source=gh&utm_medium=referral&utm_content=&utm_campaign=Badge_grade" > 
    <img src="https://app.codacy.com/project/badge/Grade/7e4271efc8894c9fab80e2f27f896a87" alt="Codacy" >
  <a></a>  
   <a href="https://github.com/Lennolium/swiftGuard/actions/workflows/black.yml" > 
    <img src="https://github.com/Lennolium/swiftGuard/actions/workflows/black.yml/badge.svg" alt="Black" >
    <a></a>
   <a href="https://github.com/Lennolium/swiftGuard/actions/workflows/github-code-scanning/codeql" > 
    <img src="https://github.com/Lennolium/swiftGuard/actions/workflows/github-code-scanning/codeql/badge.svg" 
alt="CodeQL" >
     <a></a>
  <a href="https://github.com/Lennolium/swiftGuard/actions/workflows/pyre.yml" > 
    <img src="https://github.com/Lennolium/swiftGuard/actions/workflows/pyre.yml/badge.svg?event=status" 
alt="Pyre" >
     <br>
  <a href="https://github.com/Lennolium/swiftGuard/actions/workflows/pysa.yml" > 
    <img src="https://github.com/Lennolium/swiftGuard/actions/workflows/pysa.yml/badge.svg?event=status" alt="Pysa" >
  </a> </a> </a> </a> </a>
</div>

&nbsp;

<!--- Credits -->

## Credits

This application is heavily inspired and based on project 
[usbkill](https://github.com/hephaest0s/usbkill) by Hephaestos.
I want to thank him and all the other great contributors of usbkill for
their great work, inspiration and help. I firmly believe in the
principles of the open source community, which call for the sharing and
enhancement of one another work. The purpose of this project is to
revive an abandoned project and to support others in learning and
comprehending the fundamentals of Python, Qt and macOS, and to develop
their own projects.

&nbsp;

<!--- License -->

## License

Provided under the terms of the [GNU GPL3 License](https://www.gnu.org/licenses/gpl-3.0.en.html) © Lennart Haack 2023.

See [LICENSE](https://github.com/Lennolium/swiftGuard/blob/main/LICENSE) file for details.
