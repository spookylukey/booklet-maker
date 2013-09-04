#!/usr/bin/env python
import math
import os
import sys

from PyPDF2 import PdfFileWriter, PdfFileReader


class Sheet(object):
    def __init__(self):
        self.front = PrintPage()
        self.back = PrintPage()


class PrintPage(object):
    def __init__(self):
        self.left = PageContainer()
        self.right = PageContainer()


class PageContainer(object):
    def __init__(self):
        self.page = None


def build_booklet(pages):
    # Double sized page, with double-sided printing, fits 4 of the original.
    sheet_count = int(math.ceil(len(pages) / 4.0))

    booklet = [Sheet() for i in range(0, sheet_count)]

    # Assign input pages to sheets

    def containers():
        # Yields parts of the booklet in the order they should be used.
        for sheet in booklet:
            yield sheet.back.right
            yield sheet.front.left

        for sheet in reversed(booklet):
            yield sheet.front.right
            yield sheet.back.left

    for c, p in zip(containers(), pages):
        c.page = p

    return booklet


def add_double_page(writer, page_size, print_page):
    width, height = page_size
    p = writer.insertBlankPage(width=width, height=height, index=writer.getNumPages())

    # Merge the left page
    l_page = print_page.left.page
    if l_page is not None:
        p.mergePage(l_page)

    # Merge the right page with translation
    r_page = print_page.right.page
    if r_page is not None:
        p.mergeTranslatedPage(r_page, width / 2, 0)


def print_instructions(sheets):
    instructions = """
Print pages %d to %d (however many copies you need).
Put them back in, rotated/flipped in order to print on the other side.
Print pages %d to %d.
""" % (1, len(sheets), len(sheets) + 1, len(sheets) * 2)
    print instructions


def make_booklet(input_name, output_name, blanks=0):
    reader = PdfFileReader(open(input_name, "rb"))
    pages = [reader.getPage(p) for p in range(0, reader.getNumPages())]
    for i in range(0, blanks):
        pages.insert(0, None)

    sheets = build_booklet(pages)

    writer = PdfFileWriter()
    p0 = reader.getPage(0)
    input_width = p0.mediaBox.getWidth()
    output_width = input_width * 2
    input_height = p0.mediaBox.getHeight()
    output_height = input_height

    page_size = (output_width, output_height)
    # We want to group fronts and backs together.
    for sheet in sheets:
        add_double_page(writer, page_size, sheet.back)

    for sheet in sheets:
        add_double_page(writer, page_size, sheet.front)

    writer.write(open(output_name, "wb"))
    print_instructions(sheets)


USAGE = """
Converts a PDF document into a booklet form, by re-ordering pages and
combining into double sized pages suitable for double-sided printing.

Usage:

booklet_maker.py input.pdf output.pdf [blank pages to insert at start]
"""

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print USAGE
        sys.exit(1)

    if len(sys.argv) == 4:
        blanks = int(sys.argv[3])
    else:
        blanks = 0
    make_booklet(sys.argv[1], sys.argv[2], blanks)
