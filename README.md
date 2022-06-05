# polestar-manual

Convert the online Polestar 2 manual into a PDF.

Needs a recent stable version of the **chromium** browser (not chrome).

```
usage: main.py [-h] [--url URL] [--chromium-binary CHROMIUM_BINARY] [--keep-tmp-files] [--output OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --url URL             Base URL [default: https://www.polestar.com/de/manual/polestar-2/2022]
  --chromium-binary CHROMIUM_BINARY
                        Custom chromium binary [default: query the operating system]
  --keep-tmp-files      Don't delete temporary files
  --output OUTPUT       Output filename [default: './<car model> - <model year>.pdf']
```

## Step by step instructions

Using bash on Ubuntu:

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

4. Make sure that a recent stable version of chromium is available, either
   installed in the system or as standalone download. In my setup, I fetched a
   standalone version like this:

   ```
   (.venv) $ curl -o 982481-chrome-linux.zip https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F982481%2Fchrome-linux.zip?alt=media
   (.venv) $ unzip 982481-chrome-linux.zip -d 982481/
   ```

5. Run the script, optionally pointing to the standalone chromium binary:

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
