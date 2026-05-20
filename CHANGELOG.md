# v3.0.1
- Added footer to show bindings, replacing the top row.
- Dedicated the top row for information only.
- Hid EOL versions by default.
- Added compile script to compile in nuitka.

# v3.0.0
- Began migration to Python textual from raw bash script.
- Changed to menu style for flexibility in choice for installing.
- Disabling GIL and JIT made exclusive because JIT is unstable without GIL, the ability to pass both options is disabled by Python in 3.14+ anyway. 
- Changed release searching method from parsing the html from www.python.org to directly searching the Git repository from https://github.com/python/cpython.git.

# v2.1.1
- Added option to disable GIL and add JIT compiler for python 3.13 onwards

# v2.1.0
- Renamed UpdatePython.sh to main.sh to avoid confusion
- Adapted to gzip encoding from www.python.org

# v2.0.0
- Changed parallel installation to one by one installation since compiling with a few threads is really slow
- A confirmation will now be needed before continuing the installation

# v1.0.0
First working version
