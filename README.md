# polestar-manual

Convert the online Polestar 2 manual into a PDF.

```
usage: main.py [-h] [--url URL] [--chrome-binary CHROME_BINARY] [--keep-tmp-files] [--output OUTPUT]

optional arguments:
  -h, --help            show this help message and exit
  --url URL             Base URL [default: https://www.polestar.com/de/manual/polestar-2/2022]
  --chrome-binary CHROME_BINARY
                        Custom chrome binary [default: query the operating system]
  --keep-tmp-files      Don't delete temporary files
  --output OUTPUT       Output filename [default: './<car model> - <model year>.pdf']
```