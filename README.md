# Python Updater for Ubuntu

This script updates all active releases of Python, even the pre-release ones. This is for you who likes building things from source because mental health is not a thing for you.

For the change log please check [CHANGELOG.md](./CHANGELOG.md)

---
# Future Plan

**Feel free to contribute your code, if anyone sees this at all.**

- Update when I feel annoyed of a feature


---

## How does this work?
1. Dependencies are checked. The list comes from the [developer's guide of Python](https://devguide.python.org/getting-started/setup-building).
2. Using git ls-remote, the releases are taken and compiled into a table.
3. Your python version is checked, then compared to the newest version that is available.
4. You would be able to select the specific version and update it according to your needs. All versions are installed with `altinstall`.

**Note: All python will be installed in `/usr/local/bin` so it doesn't interfere with the system's python3 (For noobs: Don't change the system python version, it breaks things).**

---
## Tutorial

> **Note:** `main.sh` is deprecated and will be removed in a future release. Use `main.py` instead.

### For Ubuntu 24.04 or after:
#### First time only:
Go to `Software and Updates` and select `Source Code` under `Ubuntu Software`

Then install dependencies:
```shell
sudo apt build-dep python3
sudo apt install python3-pip
pip install textual rich
```
#### Run:
```shell
python3 main.py
```

### For Ubuntu 23.10 or before:
#### First time only:
```shell
sudo bash -c 'CODENAME=$(grep -oP "CODENAME=\K\w+" < /etc/lsb-release); echo "deb-src http://archive.ubuntu.com/ubuntu/ $CODENAME main restricted" >> /etc/apt/sources.list'
```

Then install dependencies:
```shell
sudo apt build-dep python3
sudo apt install python3-pip
pip install textual rich
```
#### Optional:
```shell
sudo su  # Activate root if you don't want to type passwords
```

#### Run:
```shell
python3 main.py
```

### Usage
| Key | Action |
|-----|--------|
| `↑` / `↓` | Navigate versions |
| `Enter` | Select target version to install |
| `I` | Install selected version |
| `1` | Toggle PGO (Profile-Guided Optimization) |
| `2` | Toggle LTO (Link-Time Optimization) |
| `3` | Toggle GIL (disable GIL, 3.13+ only) |
| `4` | Toggle JIT (experimental, 3.13+ only) |
| `R` | Refresh version list |
| `Ctrl+C` | Quit |

### For Windows:
1. Go to Windows app store
2. Download your Python version
3. UPDATE IT WITH THE UPDATE BUTTON
