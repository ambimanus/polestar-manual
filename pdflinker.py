import sys
import os
import json
import argparse

import PyPDF2


def build_chapter_map(workdir, filemap, tocpdf='toc.pdf'):
    root_url = None
    # Read chapter lengths
    chapter_lengths = {}
    for url, pdf in filemap.items():
        reader = PyPDF2.PdfFileReader(os.path.join(workdir, pdf))
        chapter_lengths[url] = reader.getNumPages()
        if pdf == tocpdf:
            # this is our project root
            # save the url for convenience, we need it later on
            root_url = url
    # Read the order for all links as they occur in toc.pdf
    tocreader = PyPDF2.PdfFileReader(os.path.join(workdir, tocpdf))
    links = []
    for i in range(tocreader.getNumPages()):
        page = tocreader.getPage(i)

        if '/Annots' not in page: continue
        for annot in page['/Annots']:
            annot_obj = annot.getObject()
            # print(f'[+] annot: {annot_obj}')
            if '/A' not in annot_obj:
                # not a link
                continue
            link = annot_obj["/A"]["/URI"]
            if link in filemap.keys():
                links.append(link)
                # print(f'[+] Found link: {link}')
            else:
                print(f'[!] Skipped link: {link}')
    # Build chapter map
    chapter_indexes = {}
    current_index = chapter_lengths[root_url] # start right behind the toc
    for url in links:
        if url not in chapter_indexes:
            chapter_indexes[url] = current_index
            current_index += chapter_lengths[url]
        # else:
        #     print(f'[+] Duplicate chapter: {url}')
    return root_url, links, chapter_indexes

def build_manual(workdir, outdir, outfilename):
    with open(os.path.join(workdir, 'filemap.json')) as ffm:
        filemap = json.load(ffm)
    with open(os.path.join(workdir, 'toc.json')) as ftj:
        chaptermap = json.load(ftj)
    with open(os.path.join(workdir, 'topics.json')) as ftsj:
        topics = json.load(ftsj)

    # Generate titel --> url map
    urlmap = {chap: url for url, chap in chaptermap.items()}

    # Build chapter pages map
    root_url, links, chapter_indexes = build_chapter_map(workdir, filemap)

    # Prepare output document
    writer = PyPDF2.PdfFileWriter()

    # Add toc file and replace hyperlinks with internal links
    internal_links = {}
    bookmarks = {}

    tocfname = filemap[root_url]
    print(f'[+] Adding toc file: "{tocfname}"')
    tocreader = PyPDF2.PdfFileReader(os.path.join(workdir, tocfname))
    for i in range(tocreader.getNumPages()):
        page = tocreader.getPage(i)
        replaced_annot_ids = []
        if '/Annots' not in page:
            continue
        for annot_idx, annot in enumerate(page['/Annots']):
            annot_obj = annot.getObject()
            # print(f'[+] annot: {annot_obj}')
            if '/A' not in annot_obj:
                # not a link
                # print(f'[+] Skipping annot: {annot_obj}')
                continue
            # {'/Type': '/Annot', '/Subtype': '/Link', '/F': 4, '/Border': [0, 0, 0], '/Rect': [54.52146, 551.38593, 457.48486, 581.40179], '/A': {'/Type': '/Action', '/S': '/URI', '/URI': 'https://www.polestar.com/de/manual/polestar-2/2022/article/Dachtr%C3%A4ger*/'}, '/StructParent': 100667}
            link_url = annot_obj['/A']['/URI']
            link_rect = annot_obj['/Rect']
            if link_url in chapter_indexes:
                chapter_index = chapter_indexes[link_url]
                chapter_title = chaptermap[link_url]
                # Prepare internal link (will be created later)
                internal_links[link_url] = (i, chapter_index, link_rect)
                # print(f'[+] link: {(i, chapter_index, link_rect)}')
                # Prepare bookmark (will be created later)
                bookmarks[chapter_title] = chapter_index
                # print(f'[+] bookmark: {(chapter_title, chapter_index)}')
                # Prepace annot removal
                replaced_annot_ids.append(annot_idx)
        # Delete collected annots from page
        for annot_idx in sorted(replaced_annot_ids, reverse=True):
            # print(f'Deleting annot #{annot_idx} {page["/Annots"][annot_idx].getObject()}')
            del page['/Annots'][annot_idx]
        # Add current page to output
        writer.addPage(page)

    print('[+] Adding chapters')
    added_chapters = []
    for chapter_url in links:
        if chapter_url not in added_chapters:
            chfname = filemap[chapter_url]
            # print(f'[+] Adding chapter: "{chfname}"')
            chreader = PyPDF2.PdfFileReader(os.path.join(workdir, chfname))
            for i in range(chreader.getNumPages()):
                writer.addPage(chreader.getPage(i))
            added_chapters.append(chapter_url)

    # Insert internal links
    print('[+] Adding internal links')
    for srcpage, dstpage, link_rect in internal_links.values():
        writer.addLink(srcpage, dstpage, link_rect)

    # Add bookmarks
    print('[+] Adding bookmarks')
    for section in topics:
        section_bm = None
        for subsection in section['subsections']:
            subsection_bm = None
            for item in subsection['items']:
                item_url = urlmap[item]
                if item_url in chapter_indexes:
                    dstpg = chapter_indexes[item_url]
                    if section_bm is None:
                        # print(f'Bookmark: section "{section["text"]}" --> page {dstpg}')
                        section_bm = writer.addBookmark(section['text'], dstpg)
                    if subsection_bm is None:
                        # print(f'Bookmark: subsection "{section["text"]}" --> page {dstpg}')
                        subsection_bm = writer.addBookmark(subsection['text'],
                                dstpg, parent=section_bm)
                    # print(f'Bookmark: item "{item}" --> page {dstpg}')
                    writer.addBookmark(item, dstpg, parent=subsection_bm)
    # Activate bookmark panel on startup
    writer.setPageMode('/UseOutlines')

    # Add metadata
    git_url = 'https://github.com/ambimanus/polestar-manual'
    writer.addMetadata(
        {
            '/Title': chaptermap[root_url],
            '/Author': git_url,
            '/Subject': f'Generated from {root_url}'
        }
    )

    # Write output file
    sys.setrecursionlimit(10000) # FIXME
    if outfilename is None:
        outfilename = '.'.join((chaptermap[root_url], 'pdf'))
    outfile = os.path.join(outdir, outfilename)
    print(f'[+] Writing output file: "{outfile}"')
    os.makedirs(outdir, exist_ok=True)
    with open(outfile, 'wb') as f:
        writer.write(f)


def make_parser():
    parser = argparse.ArgumentParser()

    parser.add_argument('--workdir', required=True)
    parser.add_argument('--output', help="Output filename [default: './<car model> - <model year>.pdf']")

    return parser


if __name__ == '__main__':
    parser = make_parser()
    args = parser.parse_args()

    # Set output filename
    if args.output is not None:
        outdir, outfilename = os.path.split(args.output)
    else:
        outdir, outfilename = '.', None

    build_manual(args.workdir, outdir, outfilename)