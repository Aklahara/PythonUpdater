# Python Updater for Ubuntu

This script updates all active releases of Python, even the pre-release ones. This is for people who can't use [ppa:deadsnakes](https://launchpad.net/~deadsnakes/+archive/ubuntu/ppa) because you are an update freak like me and not using LTS.

If you have a script that runs on an end of life Python version, it's best to find another repository that hasn't been abandoned for over 5 years.

For the change log please check [CHANGELOG.md](./CHANGELOG.md)

---
# Future Plan

**Feel free to contribute your code, if anyone sees this at all.**

- Passing arguments such as `./main.sh 3.12` will check the specific version only


---

## How does this work?
1. Dependencies are either updated or installed. The list comes from the [developer's guide of Python](https://devguide.python.org/getting-started/setup-building).
2. Using wget, release information is extracted from the Python [download](https://www.python.org/downloads/) and [pre-release](https://www.python.org/download/pre-releases/) pages.
3. Using a bunch of greps, a list of all releases is generated. The list is sorted with `sort -Vr`, so the newest version is `head -n 1`.
4. Your python version is checked, if it does not exist, the version will be `None`.
5. All active Python versions will be updated/installed based on that information.

**Note: All python will be installed in `/usr/local/bin` so it doesn't interfere with the system's python3 (For noobs: Don't change the system python version, it breaks things).**

---
## Tutorial
### For Ubuntu:
#### First time only:
```shell
sudo bash -c 'CODENAME=$(grep -oP "CODENAME=\K\w+" < /etc/lsb-release); echo "deb-src http://archive.ubuntu.com/ubuntu/ $CODENAME main restricted" >> /etc/apt/sources.list'
```
#### Optional:
```shell
sudo su  # Activate root if you don't want to type passwords
```

#### Run:
```shell
sudo chmod +x main.sh
sudo chmod +x InstallPython.sh
./main.sh
```

### For Windows:
1. Go to Windows app store
2. Download your Python version
3. UPDATE IT WITH THE UPDATE BUTTON
