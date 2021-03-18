#!/usr/bin/env python3
import db_logic
for ep_id in db_logic.get_new_eps_from_db().keys():
    print(ep_id)
    db_logic.mark_ep_as_downloaded(ep_id)

