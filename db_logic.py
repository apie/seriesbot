#!/usr/bin/env python3

import os
from pydblite import Base

SCRIPT_DIR = os.path.dirname(os.path.realpath(__file__))

show_db = Base(os.path.join(SCRIPT_DIR, 'show.db'))
show_db.create('show_id', 'name', 'latest_ep_id', mode="open")

ep_db = Base(os.path.join(SCRIPT_DIR, 'episode.db'))
ep_db.create('ep_id', 'show_id', 'season', 'number', 'name', 'airdate', 'downloaded', mode="open")


def get_shows_from_db():
    shows = {}
    for rec in show_db:
        shows[rec['show_id']] = {
            'name': rec.get('name'),
            'latest_ep': rec.get('latest_ep_id'),
        }
    return shows


def save_shows_in_db(shows):
    db = show_db
    for show_id, value in shows.items():
        rec = db("show_id") == show_id
        if not rec:
            rec_id = db.insert(show_id=show_id)
            db.commit()
            rec = db[rec_id]
        db.update(rec, name=value.get('name'), latest_ep_id=value.get('latest_ep'))
    db.commit()


def get_new_eps_from_db():
    eps = {}
    for rec in ep_db:
        if rec.get('downloaded'):
            continue
        eps[rec['ep_id']] = {
            'show_id': rec.get('show_id'),
            'season': rec.get('season'),
            'number': rec.get('number'),
            'name': rec.get('name'),
            'airdate': rec.get('airdate'),
            'downloaded': rec.get('downloaded'),
        }
    return eps


def save_eps_in_db(eps):
    db = ep_db
    for ep_id, value in eps.items():
        rec = db("ep_id") == ep_id
        if not rec:
            rec_id = db.insert(ep_id=ep_id)
            db.commit()
            rec = db[rec_id]
        db.update(rec,
                  show_id=value.get('show_id'),
                  season=value.get('season'),
                  number=value.get('number'),
                  name=value.get('name'),
                  airdate=value.get('airdate'),
                  downloaded=value.get('downloaded')
                  )
    db.commit()


def get_rec(ep_id):
    db = ep_db
    rec = db("ep_id") == ep_id
    if not rec:
        rec_id = db.insert(ep_id=ep_id)
        db.commit()
        rec = db[rec_id]
    return rec


def mark_ep_as_downloaded(ep_id, downloaded=True):
    rec = get_rec(ep_id)
    db = ep_db
    db.update(rec, downloaded=downloaded)
    db.commit()


def list_show_db():
    db = show_db
    for rec in db:
        print(rec)


def list_ep_db():
    db = ep_db
    for rec in db:
        print(rec)
