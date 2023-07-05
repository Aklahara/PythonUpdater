# Python Updater

This script updates all active releases of Python, even the pre-release ones.

If you have a script that runs on an old Python version, it's best to find another repository that hasn't been abandoned for over 5 years.

---
**Feel free to contribute for your code, if anyone sees this at all.**

---

## How does this work?
1. Using curl, release information is extracted from the Python [download](https://www.python.org/downloads/) and [pre-release](https://www.python.org/download/pre-releases/) pages.
2. Using a bunch of greps, a list of all releases is generated. The list is sorted with `sort -Vr`, so the newest version is `head -n 1`.
3. Your python version is checked, if it does not exist, the version will be `None`.
4. All active Python versions will be updated/installed based on that information.

### For Ubuntu:
```shell
sudo chmod +x UpdatePython.sh
./UpdatePython.sh
```

### For Windows:
1. Go to Windows app store
2. Download your Python version
3. UPDATE IT WITH THE UPDATE BUTTON