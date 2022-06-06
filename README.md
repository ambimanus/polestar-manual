# polestar-manual

Convert the online Polestar 2 manual into a PDF.

Needs a recent stable version of the **chromium** browser (not chrome).

```
usage: main.py [-h] --chromium-binary CHROMIUM_BINARY [--url URL] [--keep-tmp-files] [--output OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --chromium-binary CHROMIUM_BINARY
                        Path to chromium binary 982481 (101.0.4951.0)
  --url URL             Base URL [default: https://www.polestar.com/de/manual/polestar-2/2022]
  --keep-tmp-files      Don't delete temporary files
  --output OUTPUT       Output filename [default: './<car model> - <model year>.pdf']
```

## Step by step instructions

Using bash on Ubuntu. Don't do this as `root`, otherwise chromium won't start later on. Instead, create a normal user and use `sudo` in step 5.

1. Get the code, i.e. clone the repository into a local folder:

   ```
   $ git clone https://github.com/ambimanus/polestar-manual.git
   ```

2. Create a virtual environment:

   ```
   $ cd polestar-manual
   $ mkdir .venv && python3 -m venv .venv
   ```

3. Activate the virtual environment and install dependencies:

   ```
   $ source .venv/bin/activate
   (.venv) $ pip install -r requirements.txt
   ```

4. Make sure that a recent stable version of chromium 101.0.4951.0 is
   available. In my setup, I fetched a standalone version like this:

   ```
   (.venv) $ curl -o 982481-chrome-linux.zip https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F982481%2Fchrome-linux.zip?alt=media
   (.venv) $ unzip 982481-chrome-linux.zip -d 982481/
   ```

5. If you are running a fresh LXC container, you'll most likely need to install some chromium dependencies:
   
   ```
   (.venv) $ sudo apt install libasound2 libatk-bridge2.0-0 libatk1.0-0 libatspi2.0-0 libcairo2 libcups2 libdbus-1-3 libdrm2 libexpat1 libgbm1 libgcc1 libgdk-pixbuf2.0-0 libglib2.0-0 libgtk-3-0 libnspr4 libnss3 libpango-1.0-0 libpangocairo-1.0-0
   ```

6. Run the script while pointing to the chromium binary:

   ```
   (.venv) $ python main.py --chromium-binary 982481/chrome-linux/chrome
   ```

## Diff report generator

Compares two topic maps (either via json file or via url) and generates a
HTML-formatted report.

```
usage: jsondiff.py [-h] [--fromurl FROMURL] [--tourl TOURL] [--fromfile FROMFILE]
                   [--tofile TOFILE] [--output OUTPUT] [--chromium-binary CHROMIUM_BINARY]

optional arguments:
  -h, --help            show this help message and exit
  --fromurl FROMURL     URL to compare
  --tourl TOURL         URL to compare
  --fromfile FROMFILE   JSON file to compare
  --tofile TOFILE       JSON file to compare
  --output OUTPUT       Output filename [default: ./diff.html]
  --chromium-binary CHROMIUM_BINARY
                        Custom chromium binary [default: query the operating system]

You must provide either fromurl/tourl or fromfile/tofile, not both.
```
