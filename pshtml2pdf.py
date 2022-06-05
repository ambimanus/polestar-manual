import os
import re
import json
import base64
from urllib.parse import unquote

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import JavascriptException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.core.utils import ChromeType


def send_devtools(driver, cmd, params={}):
    sid = driver.session_id
    resource = f'/session/{sid}/chromium/send_command_and_get_result'
    url = driver.command_executor._url + resource
    body = json.dumps({'cmd': cmd, 'params': params})
    response = driver.command_executor._request('POST', url, body)
    if response.get('status'):
        raise Exception(response.get('value'))
    return response.get('value')

def setup_driver(path, chrome_binary=None):
    driver_options = Options()
    driver_options.add_argument('--headless')
    driver_options.add_argument('--disable-gpu')
    # Make given chrome_binary visible to webdriver-manager
    if chrome_binary is not None:
        chrome_binary_path = os.path.dirname(chrome_binary)
        os.environ['PATH'] = ':'.join((chrome_binary_path, os.environ['PATH']))
        driver_options.binary_location = chrome_binary
    driver_manager = ChromeDriverManager(chrome_type=ChromeType.CHROMIUM,
                                         version="101.0.4951.41")
    driver_service = Service(driver_manager.install())
    driver = webdriver.Chrome(service=driver_service, options=driver_options)
    # Set script timeout to 5mins
    driver.set_script_timeout(300)
    # Establish browser context
    driver.get(path)
    return driver

def js(driver, script, errors, execute_async=False, args=[]):
    try:
        if execute_async:
            if script.endswith(';'):
                script = script[:-1]
            script = f'var sel_cb = arguments[0]; sel_cb({script});'
            # print(f'[+] Executing async script: {script}')
            return driver.execute_async_script(script, *args)
        else:
            # print(f'[+] Executing script: {script}')
            return driver.execute_script(script, *args)
    except JavascriptException as jse:
        print(f'[!] Error while executing script: {jse}')
        errors.append((script, jse.__repr__()))

# https://stackoverflow.com/a/65360714
def txt2filename(txt, chr_set='printable'):
    """Converts txt to a valid filename.

    Args:
        txt: The str to convert.
        chr_set:
            'printable':    Any printable character except those disallowed on Windows/*nix.
            'extended':     'printable' + extended ASCII character codes 128-255
            'universal':    For almost *any* file system. '-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
    """

    FILLER = '-'
    # Maximum length of filename is 255 bytes in Windows and some *nix flavors.
    MAX_LEN = 255

    # Step 1: Remove excluded characters.
    # 127 is unprintable, the rest are illegal in Windows.
    BLACK_LIST = set(chr(127) + r'<>:"/\|?*')
    white_lists = {
        'universal': {'-.0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'},
        # 0-32, 127 are unprintable
        'printable': {chr(x) for x in range(32, 127)} - BLACK_LIST,
        'extended' : {chr(x) for x in range(32, 256)} - BLACK_LIST,
    }
    white_list = white_lists[chr_set]
    result = ''.join(x
                     if x in white_list else FILLER
                     for x in txt)

    # Step 2: Device names, '.', and '..' are invalid filenames in Windows.
    DEVICE_NAMES = 'CON,PRN,AUX,NUL,COM1,COM2,COM3,COM4,' \
                   'COM5,COM6,COM7,COM8,COM9,LPT1,LPT2,' \
                   'LPT3,LPT4,LPT5,LPT6,LPT7,LPT8,LPT9,' \
                   'CONIN$,CONOUT$,..,.'.split()
    if result in DEVICE_NAMES:
        result = f'-{result}-'

    # Step 3: Truncate long files while preserving the file extension.
    if len(result) > MAX_LEN:
        if '.' in txt:
            result, _, ext = result.rpartition('.')
            ext = '.' + ext
        else:
            ext = ''
        result = result[:MAX_LEN - len(ext)] + ext

    # Step 4: Windows does not allow filenames to end with '.' or ' '
    # or begin with ' '.
    result = re.sub(r'^[. ]', FILLER, result)
    result = re.sub(r' $', FILLER, result)

    return result

def waitforpage(driver, timeout=10):
    selector_toc = 'div[data-testid="owners-manual-accordion"]'
    selector_chp = 'div[data-testid="article-content"]'
    selector = ','.join((selector_toc, selector_chp))
    WebDriverWait(driver, timeout).until(
        EC.visibility_of_element_located((By.CSS_SELECTOR, selector))
    )

def prepare_page(driver, errors):
    # Wait for content to load
    waitforpage(driver)

    # Inject javascript functions
    lhp = './layout-hacks.js'
    # print('[|] Injecting javascript functions')
    with open(lhp) as layout_hacks:
        js(driver, layout_hacks.read(), errors)

    # Setup page layout
    cssrules = [
        '@page { size: B5; orphans:4; widows:2; }',
        'h2 { page-break-after : avoid }',
        'table { page-break-inside : avoid }',
        'div.segment { page-break-inside : avoid }',
        'div.subsegment { page-break-inside : avoid }',
        'p { page-break-inside : avoid }',
        'li { page-break-inside : avoid }',
    ]
    for css in cssrules:
        js(driver, f'hack_injectcss("{css}");', errors)

def print_to_pdf(driver, print_options={}):
    # https://chromedevtools.github.io/devtools-protocol/tot/Page/#method-printToPDF
    # inch_factor = 25.4
    calculated_print_options = {
        'landscape': False,
        'displayHeaderFooter': False,
        'printBackground': True,
        # 'scale': 1.0,
        # 'paperWidth': 148 / inch_factor,
        # 'paperHeight': 210 / inch_factor,
        # 'marginTop': 5 / inch_factor,
        # 'marginBottom': 5 / inch_factor,
        # 'marginLeft': 5 / inch_factor,
        # 'marginRight': 5 / inch_factor,
	    'preferCSSPageSize': True,
    }
    calculated_print_options.update(print_options)
    res = send_devtools(driver, 'Page.printToPDF', calculated_print_options)
    return base64.b64decode(res['data'])

def fetch_toc(driver, url):
    chapters = {}
    errors = []

    # Navigate to destination
    driver.get(url)

    # Preprocessing
    prepare_page(driver, errors)

    # Setup page layout
    js(driver, 'hack_injectcss("@page { margin: 5mm; }");', errors)
    # Fetch version of the manual, i.e. car model
    carmodel = js(driver, 'return hack_carmodel();', errors,
                    execute_async=False).strip()
    # Remove unnessecary elements
    js(driver, 'hack_remove_unnecessary_toc_elems();', errors)
    # Expand the accordion (twice, to get both levels)
    print('[|] Expanding sections')
    js(driver, 'hack_expand_sections();', errors, execute_async=True)
    print('[|] Expanding subsections')
    js(driver, 'hack_expand_sections();', errors, execute_async=True)
    # Scrape the embedded links
    ret = js(driver, 'return hack_scrape_links();', errors)
    for title, url in ret:
        if url not in chapters:
            chapters[url] = title
    print(f'[|] Found {len(chapters)} unique links')
    # Scrape the topic hierarchy
    topics = js(driver, 'return hack_scrape_hierarchy();', errors)
    # Print to PDF
    pdf = print_to_pdf(driver)
    # Return all collected data
    return pdf, carmodel, topics, chapters, errors

def fix_url(url, relative=True):
    if relative:
        url = url[24:]
    safechars = [
        '%26',  # &
        '%2c',  # ,
        '%2f',  # /
        '%c2',  # Â
        '%a0',  # '	 '
    ]
    # "Escape" our safechars
    for sc in safechars:
        url = url.replace(sc.upper(), sc.upper().replace('%', 'SAFECHAR'))
        url = url.replace(sc.lower(), sc.lower().replace('%', 'SAFECHAR'))
    # Unquote
    url = unquote(url)
    # "Unescape" our safechars
    url = url.replace('SAFECHAR', '%')

    return url

def fetch_chapter(driver, tocurl, chapurl):
    errors = []

    # Navigate to chapter by simulating user behavior to prevent a 502 error
    driver.get(tocurl)
    waitforpage(driver)
    relurl = fix_url(chapurl)
    script = 'document.querySelector(`a[data-testid^="seo-hidden-article-link-"][href="${arguments[0]}"]`).click();'
    # print(f'[|] Simulating click: {script}')
    js(driver, script, errors, args=[relurl, ])

    # Preprocessing
    prepare_page(driver, errors)

    # Setup page layout
    js(driver, 'hack_injectcss("@page { margin: 15mm; }");', errors)
    # Remove unnessecary elements
    js(driver, 'hack_remove_unnecessary_chapter_elems();', errors)

    # Print to PDF
    pdf = print_to_pdf(driver)
    # Return all collected data
    return pdf, errors

def fetch_manual(tocurl, workdir, chrome_binary=None):
    error_dict = {}
    filemap = {}
    tocpdfname, tocjsonname = 'toc.pdf', 'toc.json'
    topicsjsonname, filemapjsonname = 'topics.json', 'filemap.json'

    # Setup driver
    driver = setup_driver(tocurl, chrome_binary=chrome_binary)

    # Get toc
    fp = os.path.join(workdir, tocpdfname)
    print(f'[+] Fetching {tocurl} --> "{fp}"')
    result, root_title, topics, chapters, errors = fetch_toc(driver, tocurl)
    with open(fp, 'wb') as file:
        file.write(result)
    if len(errors) > 0:
        error_dict[tocurl] = errors
    # add tocurl to chapters and filemap
    chapters[tocurl] = root_title
    filemap[tocurl] = tocpdfname
    fpjson = os.path.join(workdir, tocjsonname)
    print(f'[+] Storing link map --> "{fpjson}"')
    with open(fpjson, 'w') as fp:
        json.dump(chapters, fp)
    ftjson = os.path.join(workdir, topicsjsonname)
    print(f'[+] Storing topic hierarchy --> "{ftjson}"')
    with open(ftjson, 'w') as ft:
        json.dump(topics, ft)

    # Get additional pages
    fetch_amount = len(chapters) - 1
    for i, chapter_url in enumerate(chapters.keys()):
        if chapter_url == tocurl:
            continue
        num = i + 1
        title = chapters[chapter_url] + '.pdf'
        fn = txt2filename(title)
        fp = os.path.join(workdir, fn)
        filemap[chapter_url] = fn
        print(f'[{num}/{fetch_amount}] Fetching {chapter_url} --> "{fp}"')
        result, errors = fetch_chapter(driver, tocurl, chapter_url)
        retry_counter = 0
        while len(errors) > 0 and retry_counter < 2:
            # errfp = os.path.join(workdir, f'err_{retry_counter:02}_{fn}')
            # print(f'[!] Storing erroneous file --> "{errfp}"')
            # with open(errfp, 'wb') as file:
            #     file.write(result)
            retry_counter += 1
            # # Prevent cloudflare error
            # time.sleep(abs(random.normalvariate(5.0, 5.0)))
            print(f'[{num}/{fetch_amount}] Retry: {chapter_url} --> "{fp}"')
            result, errors = fetch_chapter(driver, tocurl, chapter_url)
        with open(fp, 'wb') as file:
            file.write(result)
        if len(errors) > 0:
            error_dict[chapter_url] = errors

    # Store file map
    fmjson = os.path.join(workdir, filemapjsonname)
    print(f'[+] Storing file map --> "{fmjson}"')
    with open(fmjson, 'w') as fp:
        json.dump(filemap, fp)

    # Shutdown driver
    driver.quit()

    # Error handling
    print()
    print(f'[!] There have been error(s) on {len(error_dict)} page(s):')
    for k, v in error_dict.items():
        print(f'[+] {k}')
        for e in v:
            print(f'[|] {e}')
    errjson = os.path.join(workdir, 'errors.json')
    print(f'[+] Storing error map --> "{errjson}"')
    with open(errjson, 'w') as fp:
        json.dump(error_dict, fp)
