""" Download a textbook from XYZ Textbooks with pages as SVGs.
"""
import argparse
import configparser
import json
import logging
from os import makedirs, path
import re

import requests
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

CONFIG_FN = 'config.ini'

config = configparser.ConfigParser()
if config.read(CONFIG_FN):
    logger.info('loaded config %s' % CONFIG_FN)


class XYZScraperException(Exception):
    pass


class AuthenticationError(XYZScraperException):
    pass


class SearchError(XYZScraperException):
    pass


class MultipleObjectsReturned(SearchError):
    pass


class XYZScraper:
    output_dir = None

    section_manifest = None

    _session = None
    _secure_url = 'https://www.xyztextbooks.com'
    _base_url = 'http://www.xyztextbooks.com'

    def __init__(self, username: str, password: str, output_dir: str):
        _dir = path.realpath(path.expanduser(output_dir))
        makedirs(_dir, exist_ok=True)
        self.login(username, password)
        self.output_dir = _dir

    def get_book(self, book_isbn_13: str):
        book_details = self.get_book_details(book_isbn_13)
        self.get_all_sections(book_details['id'], book_details['sections'])

    # def config_interactive(self):
    #     self.section_manifest = config.get('scraper', 'manifest')
    #     book_id = input('book id (name of the book): ')
    #     user = input('xyz user (your email): ')
    #     password = input('xyz password: ')
    #     output_dir = input('folder to place downloaded files: ')

    def login(self, username, password):
        self._session = requests.Session()
        self._session.headers['user-agent'] = ('Mozilla/5.0 (Macintosh; Intel '
                                               'Mac OS X 10_10_1) AppleWebKit/537.36 '
                                               '(KHTML, like Gecko) Chrome/41.0.2227.1 '
                                               'Safari/537.36')
        self._session.headers['origin'] = self._base_url
        self._session.get(self._secure_url + '/login')
        r = self._session.post(url=self._secure_url + '/ajax/login/ProcessLogin', data={
            'user': username,
            'password': password,
            'keep_logged_in': 1,
        })

        if "danger" in r.text or r.status_code != 200:
            logger.error('there was a problem logging in...')
            logger.error(r.text)
            raise AuthenticationError()
        else:
            logger.debug('login successful')

    def get_book_details(self, search_string):
        """ Resolve a book's url to it's ID
        :return int book_id
        """
        search_results = self.search(search_string)
        final_path_part = search_results[0].rstrip('/').split('/')[-1]
        r = self._session.get(self._base_url + '/ebook/title/' + final_path_part)
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        # do we need this?
        book_id = soup.find(id='current_book_id').attrs['value']
        section_links = soup.find_all(id=re.compile('^navlink_sec_'))
        section_ids = [l.attrs['id'].split('_')[2] for l in section_links]
        return {
            'id': book_id,
            'sections': section_ids
        }

    def search(self, search_string, max_results=1):
        """ Search the catalog, returning the results
        :param search_string: query
        :returns: array of urls """
        url = self._base_url + '/searchresults'
        r = self._session.post(url + '/searchresults',
                               headers={'referrer': url},
                               data={'search_string': search_string})
        soup = BeautifulSoup(r.text, 'html.parser')
        first_row = soup.find(class_='searchresult').find_all('a')
        num_results_in_row = len(first_row)
        logger.debug('query "%s" returned ±%s results' % (search_string, num_results_in_row))
        if num_results_in_row < 1:
            raise SearchError('the search "%s" returned zero results')
        if num_results_in_row > max_results:
            raise MultipleObjectsReturned('search "%s" returned more than %s result(s)--it returned %s!' %
                              (search_string, max_results, num_results_in_row))
        return [a.attrs['href'] for a in first_row]

    def load_section(self, book_id: int, section_id: int):
        _r = self._session.post(self._base_url + '/ajax/ebook/LoadEbookSection', data={
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

        _r = self._session.get(self._base_url + '/box_ebooks/%s/info.json' % box_id)
        box_info = json.loads(_r.text)
        section_data['numpages'] = box_info['numpages']
        return section_data
    
    def get_all_sections(self, book_id, section_manifest):
        for s in section_manifest:
            metadata = self.load_section(book_id, s)
            doc_path = metadata['box_document_path']
            pages = metadata['numpages']
            metadata = metadata['section']  # let's avoid arthritis

            # summary, review and test sections do not have names, and are
            # marked as section #0
            if not metadata['name'] and metadata['section_number'] == '0':
                metadata['name'] = 'Summary, Review & Test'
                metadata['section_number'] = 'z'

            section_name = "%s.%s - %s" % (
                metadata['chapter_number'],
                metadata['section_number'],
                metadata['name'])

            logger.warning('working section %s' % section_name)
            section_dir = path.join(self.output_dir, section_name)
            makedirs(section_dir, exist_ok=True)

            for p in range(1, pages + 1):
                logger.debug('working page %s' % p)
                r = self._session.get(self._base_url + doc_path + '/page-%s.svg' % p)
                with open(path.join(section_dir, '%i.svg' % p), 'w+') as page_f:
                    page_f.write(r.text)

            r = self._session.get(self._base_url + doc_path + '/stylesheet.css')
            with open(path.join(section_dir, 'stylesheet.css'), 'w+') as stylesheet_f:
                logger.debug('writing stylesheet')
                stylesheet_f.write(r.text)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Download all pages of an XYZ textbook.')
    parser.add_argument('username', type=str, help='XYZ textbooks username')
    parser.add_argument('password', type=str, help='XYZ textbooks password')
    parser.add_argument('book_isbn', type=str, help='The ISBN-13 of your book')
    parser.add_argument('output_dir', type=str,
                        help='the output directory for the scraper')
    args = parser.parse_args()
    scraper = XYZScraper(args.username, args.password, args.output_dir)
    scraper.get_book(args.book_isbn)
