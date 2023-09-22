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
  <a href="#" > 
    <img src="https://img.shields.io/github/repo-size/Lennolium/swiftGuard?label=Repo%20Size&color=orange" alt="repo size" >
  <a></a>  
   <a href="https://github.com/Lennolium/swiftGuard/branches" > 
    <img src="https://img.shields.io/github/last-commit/Lennolium/swiftGuard?label=Last%20Updated&color=green" alt="last updated" >
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
     <a href="https://tinyurl.com/opinionoffriends" > 
    <img src="https://img.shields.io/badge/Rating-★★★★★-yellow" alt="rating" >
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
It ensures the security of your device by automatically initiating a system shutdown or hibernation whenever an 
unauthorized device is connected or a connected device is removed. It offers the flexibility to whitelist 
designated devices, to select an action to execute and to set a countdown timer, allowing to disarm the 
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
- [Installation](#installation)
- [Usage](#usage)
    - [GUI](#gui)
    - [CLI](#cli)
- [Development](#development)
- [Credits](#credits)
- [License](#license)

&nbsp;

<!--- Features -->

## Features

- __Monitoring:__ Continuously monitors USB ports for device activity.
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

<!--- Installation -->

## Installation

1. Download the latest release from the <a href="https://github.com/Lennolium/swiftGuard/releases">Releases</a> tab.
2. Open the downloaded `swiftGuard.dmg` file.
3. Drag the swiftGuard application into the Applications folder.
4. Grant necessary permissions by opening `System Preferences > 
   Security & Privacy > Privacy > Accessibility` and adding swiftGuard to 
   the list of applications. Do the same for `Automation`.
5. Open the swiftGuard application from the Applications folder.
6. swiftGuard should now appear in the macOS system tray.

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
            
**Notes:** 
- swiftGuard alerts you if devices are removed that were connected before or while the application was started,
except you add them to the whitelist. 
- Connecting new devices will always trigger an alert, if they these devices are not whitelisted.
- If you encounter any problems, please check the log file in the `~/Library/Logs/swiftGuard` folder.
- Your settings and whitelisted devices are stored in the `~/Library/Preferences/swiftGuard/swiftguard.ini` file.


&nbsp;

### CLI

You can also run swiftGuard from the command line standalone as simple Python script without GUI. This is useful if
you want to run swiftGuard on a headless system or if you want to save some system resources. You will lose the ability
to defuse the shutdown process via the GUI, but you can instead kill the swiftGuard process via the command line. 
Settings and whitelists are stored in the same location as the GUI version, and can be edited manually. 
For examples, configuration and further information, please refer to the [worker.py](https://github.com/Lennolium/swiftGuard/blob/main/src/swiftGuard/worker.py) 
file in the `src/swiftGuard` folder.

1. Open a terminal and navigate to the desired directory.
    ```bash
    cd ~/Desktop
    ```

2. Clone the repository.
    ```bash
    git clone https://github.com/Lennolium/swiftGuard.git
    ```
   
3. Navigate to the source directory.
    ```bash
    cd swiftGuard/src/swiftGuard
    ```

4. Install the requirements in a new virtual environment.
    ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip3 install -r requirements.txt
    ```

5. Run the worker.py.
    ```bash
    python3 worker.py
    ```

**Notes:**
- Settings/Whitelist: `~/Library/Preferences/swiftGuard/swiftguard.ini`
- Logs: `~/Library/Logs/swiftGuard/swiftguard.log`
   
&nbsp;

<!--- Development -->

## Development

As an open-source project, I strive for transparency and collaboration in my development process. I greatly 
appreciate any contributions members of our community can provide. Whether you are fixing bugs, proposing features, 
improving documentation, or spreading awareness - your involvement strengthens the project. Please review the 
[code of conduct](https://www.contributor-covenant.org/version/1/4/code-of-conduct/) to understand how we work together 
respectfully.

- __Bug Report:__ If you are experiencing an issue while using the application, please [create an issue](https://github.com/Lennolium/swiftGuard/issues/new/choose).
- __Feature Request:__ Make this project better by [submitting a feature request](https://github.com/Lennolium/swiftGuard/discussions/2).
- __Documentation:__ Improve our documentation by [adding a wiki page](https://github.com/Lennolium/swiftGuard/wiki).
- __Community Support:__ Help others on [GitHub Discussions](https://github.com/Lennolium/swiftGuard/discussions).


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
