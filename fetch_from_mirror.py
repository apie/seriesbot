# /usr/bin/env python3
import os
import requests
import shutil
import logging
from lxml import html
from urllib.parse import urljoin
from os.path import splitext

from new_series import print_ep
from get_subs import get_sub
import db_logic
import fetch_from_mirror_conf as settings

TIMEOUT = 10
logger = logging.getLogger(__name__)


def is_downloadable(url, auth=None):
    """
    Does the url contain a downloadable resource
    https://www.codementor.io/aviaryan/downloading-files-from-urls-in-python-77q3bs0un
    """
    # Ends with an extension
    if len(splitext(url)[1]) > 0:
        return True
    h = requests.head(url, allow_redirects=True, auth=auth)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True


def download_ep(ep_url):
    if not is_downloadable(ep_url, settings.AUTH):
        raise Exception('Not downloadable: {}'.format(ep_url))
    ep_filename = os.path.basename(ep_url)
    local_file = os.path.join(settings.DOWNLOAD_PATH, ep_filename)
    if os.path.isfile(local_file):
        return  # File exists
    try:
        ep_href_response = requests.get(ep_url, auth=settings.AUTH, stream=True)
        ep_href_response.raise_for_status()
        with open(local_file, 'wb') as ep_file:
            # print('Downloading: '+ep_filename)
            shutil.copyfileobj(ep_href_response.raw, ep_file)
    except:
        os.remove(local_file)
        raise
    print('Downloaded: ' + ep_filename)
    get_sub(local_file)
    return True


def do_fetch():
    shows = db_logic.get_shows_from_db()
    ep_names = {
        ep_id: dict(
            show_name=shows[info['show_id']]['name'],
            variants=[
                print_ep(season=info['season'], episode=info['number']),
                print_ep(season=info['season'], episode=info['number'], v=2),
            ]
        ) for ep_id, info in db_logic.get_new_eps_from_db().items()
    }

    if not ep_names:
        # No new eps
        return

    mirror_pages = []
    for mirror_url in settings.MIRROR_URLS:
        try:
            mirror_page_response = requests.get(mirror_url, auth=settings.AUTH, timeout=TIMEOUT)
            mirror_page_response.raise_for_status()
        except:
            logger.error('Error getting ' + mirror_url)
            continue
        mirror_page = html.fromstring(mirror_page_response.text)
        mirror_pages.append((mirror_page_response.url, mirror_page))
    for ep_id, ep_name in ep_names.items():
        # Need to match case insensitive. Use a workaround with translate() for Xpath 1.0
        current_url = None
        ep_folder_hrefs = None
        for url, mirror_page in mirror_pages:
            current_url = url
            for ep_name_variant in ep_name['variants']:
                search_txt = '{show} {ep_name}'.format(show=ep_name['show_name'], ep_name=ep_name_variant).replace(' ',
                                                                                                                   '.').replace(
                    "'", '').lower()
                ep_folder_hrefs = mirror_page.xpath(
                    "//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{}')]".format(
                        search_txt))
                if ep_folder_hrefs:
                    break
            if ep_folder_hrefs:
                break
        if not ep_folder_hrefs:
            continue
        # If multiple matches are there for 1 ep, take the first match
        ep_folder_href = ep_folder_hrefs[0]
        ep_folder_url = urljoin(current_url, ep_folder_href.attrib['href'])
        if is_downloadable(ep_folder_url, settings.AUTH):
            # File. Download it
            if download_ep(ep_folder_url):
                db_logic.mark_ep_as_downloaded(ep_id)
            continue
        # Otherwise it is a folder. Open it.
        ep_page_response = requests.get(ep_folder_url, auth=settings.AUTH, timeout=TIMEOUT)
        ep_page_response.raise_for_status()
        ep_page = html.fromstring(ep_page_response.text)
        ep_hrefs = ep_page.xpath(
            "//a[text() != '' and text() !='Name' and text() != 'Last modified' and text() !='Parent Directory' and text() != 'Show page in text format']")
        for ep_href in ep_hrefs:
            ep_filename = ep_href.attrib['href']
            ep_url = urljoin(ep_page_response.url, ep_filename)
            if is_downloadable(ep_url):
                if download_ep(ep_url):
                    db_logic.mark_ep_as_downloaded(ep_id)


if __name__ == '__main__':
    do_fetch()
