import os
import argparse
import json
import difflib

from pshtml2pdf import setup_driver, fetch_toc, txt2filename


def build_diff_report(fromfile, tofile, output):
    with open(fromfile) as fp:
        s1 = json.dumps(json.load(fp), indent=2).splitlines()
    with open(tofile) as fp:
        s2 = json.dumps(json.load(fp), indent=2).splitlines()

    diff = difflib.HtmlDiff(wrapcolumn=80).make_file(s1, s2, fromfile, tofile)

    # Write output file
    print(f'[+] Storing diff report --> "{output}"')
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, 'w') as f:
        f.write(diff)


def fetch_topics(url, chrome_binary=None):
    driver = setup_driver(url, chrome_binary=chrome_binary)
    _, _, topics, _, errors = fetch_toc(driver, url)
    driver.quit()

    # Error handling
    if len(errors) > 0:
        print(f'[!] There have been {len(errors)} error(s):')
        for e in errors:
            print(f'[|] {e}')

    return topics


def make_parser():
    parser = argparse.ArgumentParser(epilog='You must provide either fromurl/tourl or fromfile/tofile, not both.')

    parser.add_argument('--fromurl', help="URL to compare")
    parser.add_argument('--tourl', help="URL to compare")
    parser.add_argument('--fromfile', help="JSON file to compare")
    parser.add_argument('--tofile', help="JSON file to compare")
    parser.add_argument('--output', default="./diff.html", help="Output filename [default: %(default)s]")
    parser.add_argument('--chromium-binary', help="Custom chromium binary [default: query the operating system]")

    return parser


if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()

    if args.fromurl is not None and args.tourl is not None:
        fromfile = '.'.join([txt2filename(args.fromurl), 'json'])
        tofile = '.'.join([txt2filename(args.tourl), 'json'])
        for url, fn in zip((args.fromurl, args.tourl), (fromfile, tofile)):
            print(f'[+] Fetching {url}')
            topics = fetch_topics(url, args.chromium_binary)
            print(f'[+] Storing topic hierarchy --> "{fn}"')
            with open(fn, 'w') as fp:
                json.dump(topics, fp)
    elif args.fromfile is not None and args.tofile is not None:
        fromfile, tofile = args.fromfile, args.tofile

    build_diff_report(fromfile, tofile, args.output)
