""" Downloads a textbook from XYZ Textbooks as SVGs. To use, you must generate a
chapter manifest file. This is just a text file with a chapter ID on each line.

As of July 2016, it's possible to generate this by running the following
JavaScript in your browser;

 ids = [];
 $(".chapter").find("[id^=navlink_sec_]").each(function(index) {
   ids.push($(this).attr('id').split('_')[2]);
 });
 console.log(ids);

You may transform this JSON in to an attributes by running the following;

 echo '<paste text here>' \
  | python -m json.tool \
  | sed -E 's/[[:space:]]+"//g; s/".*//g' \
  | tail -n +2 \
  | head -n -1

"""
import requests
from os import path, makedirs
import json

section_manifest_fn = input('chapter manifest: ')
book_id = input('book id (name of the book): ')
user = input('xyz user (your email): ')
password = input('xyz password: ')
output_dir = input('folder to place downloaded files: ')

"""
{
    "result": "OK", "message": "",
    "section": {"0": "6601", "section_id": "6601", "1": "1025", "chapter_id": "1025", "2": "3", "section_number": "3",
                "3": "0", "summary": "0", "4": "Graphs of Linear Equations", "name": "Graphs of Linear Equations",
                "5": "flash_papers\/yosea_ch02_S3.pdf.swf", "flash_paper": "flash_papers\/yosea_ch02_S3.pdf.swf",
                "6": "", "introductory_videos_name": "", "7": "", "mini_lecture_image": "", "8": "",
                "additional_videos_image": "", "9": "", "errata_file": "", "10": "", "errata_text": "", "11": "",
                "crocodoc_id": "", "12": "dd993091e44e473dbfc77d177bbc8cb5",
                "crocodoc_id_interactive": "dd993091e44e473dbfc77d177bbc8cb5", "13": "2", "chapter_number": "2",
                "14": "", "chapter_label": "",
                "section_take5": ["\n\t\n\t\n\t\n\t\n\n"]},
    "has_local_box_document": True,
    "box_document_path": "\/box_ebooks\/dd993091e44e473dbfc77d177bbc8cb5",
    "user_has_closed_sidebar": "true", "chapter_toc_note": ""
}
"""


def load_section(session: requests.Session, book_id, section_id):
    _r = session.post('http://www.xyztextbooks.com/ajax/ebook/LoadEbookSection', data={
        'section_id': section_id,
        'flags': "false",
        'book_id': book_id,
    })

    section_data = json.loads(_r.text)
    for crap in ['section_supplements',
                 'section_examples',
                 'student_supplements_tab',
                 'section_problemset',
                 'all_section_examples']:
        try:
            del section_data['section'][crap]
        except KeyError:
            pass

    box_id = section_data['section']['crocodoc_id_interactive']

    _r = session.get('http://www.xyztextbooks.com/box_ebooks/%s/info.json' % box_id)
    box_info = json.loads(_r.text)
    section_data['numpages'] = box_info['numpages']
    return section_data


def load_html_page(session: requests.Session, crocodoc_id_interactive, page):
    _r = session.get('http://www.xyztextbooks.com/box_ebooks/%s/page-%i.html' % (crocodoc_id_interactive, page))
    if r.status_code == 200:
        return _r.text
    else:
        raise ValueError(str(_r))

s = requests.Session()
s.headers['user-agent'] = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/41.0.2227.1 Safari/537.36'
s.headers['origin'] = 'https://www.xyztextbooks.com'
s.get('https://www.xyztextbooks.com/login')

print('logging in...')

r = s.post(url='https://www.xyztextbooks.com/ajax/login/ProcessLogin', data={
    'user': user,
    'password': password,
    'keep_logged_in': 1,
})

if "danger" in r.text or r.status_code != 200:
    print('there was a problem logging in...')
    print()
    print(r.text)
    exit(1)

print('login successful')

with open(section_manifest_fn, 'r+') as section_manifest_fh:
    section_manifest = section_manifest_fh.readlines()

for item in section_manifest:
    section_data = load_section(s, book_id, item)

    doc_path = section_data['box_document_path']
    section_name = "%s.%s - %s" % (
        section_data['section']['chapter_number'],
        section_data['section']['section_number'],
        section_data['section']['name'])
    section_dir = path.join(output_dir, section_name)
    makedirs(section_dir, exist_ok=True)

    for p in range(1, section_data['numpages'] + 1):
        r = s.get('http://www.xyztextbooks.com' + doc_path + '/page-%s.svg' % p)
        with open(path.join(section_dir, '%i.svg' % p), 'w+') as page_f:
            page_f.write(r.text)

    r = s.get('http://www.xyztextbooks.com' + doc_path + '/stylesheet.css')
    with open(path.join(section_dir, 'stylesheet.css'), 'w+') as stylesheet_f:
        stylesheet_f.write(r.text)
