#!/usr/bin/env python3

import os
from pydblite import Base

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))


def open_db():
  db = Base(os.path.join(SCRIPT_DIR, 'series.db'))
  db.create('show', 'name', 'netflix', 'latest_ep', mode="open")
  return db

def get_shows_from_db():
  shows = {}
  for rec in open_db():
    shows[rec['show']] = {
      'name': rec.get('name'),
      'netflix': rec.get('netflix'),
      'latest_ep': rec.get('latest_ep'),
    }
  return shows

def save_shows_in_db(shows):
  db = open_db()
  for show_id, value in shows.items():
    rec = db("show") == show_id
    if not rec:
      rec_id = db.insert(show=show_id)
      rec = db[rec_id]
    db.update(rec, name=value.get('name'), latest_ep=value.get('latest_ep'), netflix=value.get('netflix'))
  db.commit()

