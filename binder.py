import argparse
import os

import cairosvg
from PyPDF2 import PdfFileMerger

from PyPDF2 import PdfFileWriter, PdfFileReader


class BookBuilder:
    """ Builds a book from downloaded SVG/ HTML files """
    input_dir = None
    output_dir = None

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = os.path.realpath(os.path.expanduser(input_dir))
        self.output_dir = os.path.realpath(os.path.expanduser(output_dir))

        os.makedirs(self.output_dir, exist_ok=True)

        converted = self.convert_pages(dry_run=True)
        self.join_pages([os.path.expanduser(p) for p in converted], self.output_dir)

    def convert_pages(self, dry_run=False):
        converted = []
        for dirpath, dirnames, filenames in os.walk(self.input_dir, followlinks=True):
            if not dirnames:
                # we are in a leaf subdir
                css_index = filenames.index('stylesheet.css')
                css_fn = None
                if css_index:
                    css_fn = filenames.pop(css_index)
                for in_f in filenames:
                    out_folder = os.path.join(self.output_dir, os.path.basename(os.path.normpath(dirpath)))
                    os.makedirs(out_folder, exist_ok=True)
                    out_fn = os.path.join(out_folder, in_f.rsplit('.')[0] + '.pdf')
                    if not dry_run:
                        self.render_page_cairo(
                            os.path.join(dirpath, in_f),
                            out_fn,
                            os.path.join(dirpath, css_fn)
                        )
                    converted.append(out_fn)
        return converted

    def bind_section(self, in_files, out_f, in_css=None):
        pass

    @staticmethod
    def render_page_cairo(in_f, out_f, css=None):
        with open(in_f, 'rb') as in_fh:
            cairosvg.svg2pdf(file_obj=in_fh, write_to=out_f)

    @staticmethod
    def join_pages(pages, output_dir):
        # Creating an object where pdf pages are appended to
        merger = PdfFileMerger()
        for page in pages:
            merger.append(PdfFileReader(open(page, 'rb')))

        # Writing all the collected pages to a file
        with open(output_dir + '.pdf', "wb") as out_fh:
            merger.write(out_fh)

    # @staticmethod
    # def render_page(in_f, out_f, css=None):
    #     if css:
    #         return HTML(in_f).write_pdf(out_f, stylesheets=[CSS(filename=css)])
    #
    #     return HTML(in_f).write_pdf(out_f, stylesheets=[CSS(filename=css)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download all pages of an XYZ textbook.')
    parser.add_argument('input_dir', type=str, help='Directory of subdirectories for input')
    parser.add_argument('output_dir', type=str, help='the output directory for the scraper')
    args = parser.parse_args()
    builder = BookBuilder(args.input_dir, args.output_dir)
    #builder.get_book(args.book_isbn)
