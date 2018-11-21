#!/usr/bin/env python3
# Get new episodes for followed series

import requests
import re
from lxml import html

import config
import db_logic

PROFILE_PAGE='https://www.tvmaze.com/users/{user_id}/{user_name}/followed'.format(
  user_id=config.TVMAZE_USER_ID,
  user_name=config.TVMAZE_USER_NAME
)
SHOW_PAGE='http://api.tvmaze.com/shows/{id}'
EP_PAGE='http://api.tvmaze.com/episodes/{id}'

def get_followed_shows():
  response = requests.get(PROFILE_PAGE)
  if response.status_code != 200:
    raise Exception('Unable to get profile page: status {}'.format(response.status_code))

  doc = html.fromstring(response.text)
  shows_a = doc.xpath("//a[contains(@href, '/shows/') and text()!='']")
  shows = {}
  for show in shows_a:
    m = re.search('[0-9]+', show.attrib['href'])
    shows[m.group(0)] = {
      'name': show.text
    }
  return shows

def update_show_list(shows):
  for show in shows.keys():
    response = requests.get(SHOW_PAGE.format(id=show))
    if response.status_code != 200:
      raise Exception('Unable to get show page: status {}'.format(response.status_code))
    resp_j = response.json()
    if resp_j['status'] == 'Ended':
      shows[show] = None
    else:
      prev_ep_href = resp_j['_links']['previousepisode']['href']
      shows[show]['latest_ep'] = prev_ep_href.split('/').pop()
  return {k: v for k, v in shows.items() if v is not None}

def save_new_eps(new_eps):
  eps = {}
  for show_id, info in new_eps.items():
      eps[info['ep_info']['id']] = dict(
        show_id=show_id,
        number=info['ep_info']['number'],
        season=info['ep_info']['season'],
        name=info['ep_info']['name'],
        airdate=info['ep_info']['airdate'],
      )
  db_logic.save_eps_in_db(eps)

def get_new_eps():
  current_shows = db_logic.get_shows_from_db()
  new_shows = update_show_list(get_followed_shows())
  db_logic.save_shows_in_db(new_shows)
  new_eps = {k: dict(show_info=v, ep_info=get_ep_info(v['latest_ep'])) for k, v in new_shows.items() if v['latest_ep'] != current_shows.get(k, {}).get('latest_ep')}
  if new_eps:
    save_new_eps(new_eps)
    return new_eps
  return {}

def get_ep_info(ep_id):
  response = requests.get(EP_PAGE.format(id=ep_id))
  if response.status_code != 200:
    raise Exception('Unable to get episode page: status {}'.format(response.status_code))
  return response.json()
 
def print_ep(season, episode):
  return 'S{season:02}E{episode:02}'.format(season=season, episode=episode)

def print_new_eps():
  for show_id, info in sorted(get_new_eps().items(), key=lambda kv: kv[1]['ep_info']['airdate']):
    print('{ep_date}: {show_name} {ep}: {ep_name}'.format(
      ep_date=info['ep_info']['airdate'],
      show_name=info['show_info']['name'],
      ep=print_ep(season=info['ep_info']['season'], episode=info['ep_info']['number']),
      ep_name=info['ep_info']['name'],
    ))
    
if __name__ == '__main__':
  print_new_eps()

