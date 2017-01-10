# xyz-scraper
Quickly and dirtily scrape a textbook from XYZ textbooks

## Why?

I have a Sony DPT-S1 and it's pretty cool. I'd like PDF copies of my 
textbooks so I don't have to carry the physical copy. Unfortunately 
one has to get their hands a little dirty to get a PDF from xyzTextbooks.

## How?

The script works from a manifest file (which you must currently 
generate yourself), grabbing the contents of every page from every 
section as an SVG. 

From here, you need to combine the files into a PDF. The best way 
I've yet found to convert these files into PDFs is 
[PhantomJS](http://phantomjs.org/).

Once every page is a PDF they may be easily merged using a 
[variety of techniques](http://stackoverflow.com/questions/2507766/merge-convert-multiple-pdf-files-into-one-pdf).
