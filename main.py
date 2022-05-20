import os
import argparse
import tempfile

import pshtml2py
import pdflinker

def make_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--url', default='https://www.polestar.com/de/manual/polestar-2/2022', help="Base URL [default: %(default)s]")
    parser.add_argument('--chrome-binary', help="Custom chrome binary [default: query the operating system]")
    parser.add_argument('--keep-tmp-files', help='Don\'t delete temporary files', action='store_true')
    parser.add_argument('--output', help="Output filename [default: './<car model> - <model year>.pdf']")

    return parser

if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()
    # print(f"Reporting command line arguments: {args}")

    # Create temporary workdir
    if args.keep_tmp_files:
        workdir = tempfile.mkdtemp()
    else:
        tdirobj = tempfile.TemporaryDirectory()
        workdir = tdirobj.name
    # print(f'[+] Storing temporary files in "{workdir}"')

    # Set output filename
    if args.output is not None:
        outdir, outfilename = os.path.split(args.output)
    else:
        outdir, outfilename = '.', None

    pshtml2py.fetch_manual(args.url, workdir, args.chrome_binary)
    pdflinker.build_manual(workdir, outdir, outfilename)