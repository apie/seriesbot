#/usr/bin/env python3
import os
import requests
from lxml import html
from urllib.parse import urljoin

from new_series import print_ep
import db_logic
import fetch_from_mirror_conf as settings

def is_downloadable(url, auth=None):
    """
    Does the url contain a downloadable resource
    https://www.codementor.io/aviaryan/downloading-files-from-urls-in-python-77q3bs0un
    """
    h = requests.head(url, allow_redirects=True, auth=auth)
    header = h.headers
    content_type = header.get('content-type')
    if 'text' in content_type.lower():
        return False
    if 'html' in content_type.lower():
        return False
    return True

ep_names = {}
shows = db_logic.get_shows_from_db()
for ep_id, info in db_logic.get_eps_from_db().items():
  if info.get('downloaded'):
    #print('Already downloaded: {}'.format(info['name']))
    continue
  ep_names[ep_id] = '{show_name} {ep}'.format(
    show_name=shows[info['show_id']]['name'],
    ep=print_ep(season=info['season'], episode=info['number']),
  )

mirror_page_response = requests.get(settings.MIRROR_URL, auth=settings.AUTH)
mirror_page_response.raise_for_status()
mirror_page = html.fromstring(mirror_page_response.text)
for ep_id, ep_name in ep_names.items():
  # Need to match case insensitive. Use a workaround with translate() for Xpath 1.0
  ep_folder_hrefs = mirror_page.xpath("//a[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), '{}')]".format(ep_name.replace(' ', '.').lower()))
  if not ep_folder_hrefs:
    continue
  # If multiple matches are there for 1 ep, take the first match
  if len(ep_folder_hrefs) > 1:
    ep_folder_href = ep_folder_hrefs[0]
  ep_page_response = requests.get(
    urljoin(mirror_page_response.url, ep_folder_href.attrib['href']), auth=settings.AUTH)
  ep_page_response.raise_for_status()
  ep_page = html.fromstring(ep_page_response.text)
  ep_hrefs = ep_page.xpath("//a[text() != '' and text() !='Name' and text() != 'Last modified' and text() !='Parent Directory' and text() != 'Show page in text format']")
  for ep_href in ep_hrefs:
    ep_filename = ep_href.attrib['href']
    ep_url = urljoin(ep_page_response.url, ep_filename)
    if not is_downloadable(ep_url, settings.AUTH):
      raise Exception('Not downloadable: {}'.format(ep_url))
    local_file = os.path.join(settings.DOWNLOAD_PATH, ep_filename)
    if os.path.isfile(local_file):
      continue # File exists
    try:
      with open(local_file, 'wb') as ep_file:
        print('Downloading: '+ep_filename)
        ep_href_response = requests.get(ep_url, auth=settings.AUTH)
        ep_href_response.raise_for_status()
        ep_file.write(ep_href_response.content)
    except:
      os.remove(local_file)
      raise
    print('Downloaded: '+ep_filename)
    db_logic.mark_ep_as_downloaded(ep_id)

