#!/usr/bin/env python3
import os
import subprocess
import shlex
import fetch_from_mirror_conf as settings

def get_all_missing_subs(directory):
    filenames = os.listdir(directory)
    # Assume subs have the same name as their matching video file
    subfiles = [os.path.splitext(f)[0] for f in filenames if os.path.splitext(f)[1] == ('.srt')]
    videofiles_without_subs = {f for f in filenames if os.path.splitext(f)[1] == '.mkv' and os.path.splitext(f)[0] not in subfiles}
    for filename in videofiles_without_subs:
        get_sub(filename)

def get_sub(filename):
    subprocess.call(
      shlex.split('{addic7ed_cli} search -bb -i -l en {filename}'.format(
        addic7ed_cli=settings.ADDIC7ED_CLI_PATH,
        filename=filename)
      ),
      cwd=settings.DOWNLOAD_PATH,
    )
#      stdout=subprocess.DEVNULL)

if __name__ == '__main__':
    get_all_missing_subs(settings.DOWNLOAD_PATH)

