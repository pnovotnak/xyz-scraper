# xyz-scraper
Quickly and dirtily scrape a textbook from XYZ textbooks

## Why?

I have a Sony DPT-S1 and it's pretty cool. I'd like PDF copies of my 
textbooks so I don't have to carry the physical copy. Unfortunately 
one has to break some eggs to get a PDF from xyzTextbooks.

## How?

1) Start from an ISBN-13 code of the book you'd like, using the `scraper.py`
script to download every page of every section. Run the command without any
parameters to get usage.
2) Use the `binder.py` script to combine these pages into a PDF.

## Can We Do Better?

Surely. CairoSVG rasterizes the SVG files, which, while making them fast to
render, doesn't allow you to interact with text without running OCR on the
output.

It's possible to use [PhantomJS](http://phantomjs.org/) instead of the 
`binder.py` script to render the PDFs, which can then be merged via the
command line using a [variety of techniques](http://stackoverflow.com/questions/2507766/merge-convert-multiple-pdf-files-into-one-pdf).
