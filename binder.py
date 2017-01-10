import argparse
import os

from weasyprint import HTML, CSS


class BookBuilder:
    """ Builds a book from downloaded SVG/ HTML files """
    input_dir = None
    output_dir = None

    def __init__(self, input_dir: str, output_dir: str):
        self.input_dir = os.path.realpath(os.path.expanduser(input_dir))
        self.output_dir = os.path.realpath(os.path.expanduser(output_dir))

        os.makedirs(self.output_dir, exist_ok=True)

        self.bind_all()

    def bind_all(self):
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
                    self.render_page(
                        os.path.join(dirpath, in_f),
                        out_fn,
                        os.path.join(dirpath, css_fn)
                    )

    def bind_section(self, in_files, out_f, in_css=None):
        pass

    @staticmethod
    def render_page(in_f, out_f, css=None):
        if css:
            return HTML(in_f).write_pdf(out_f, stylesheets=[CSS(filename=css)])

        return HTML(in_f).write_pdf(out_f, stylesheets=[CSS(filename=css)])


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download all pages of an XYZ textbook.')
    parser.add_argument('input_dir', type=str, help='Directory of subdirectories for input')
    parser.add_argument('output_dir', type=str, help='the output directory for the scraper')
    args = parser.parse_args()
    scraper = BookBuilder(args.input_dir, args.output_dir)
    scraper.get_book(args.book_isbn)
