# Copyright 2018 miruka
# This file is part of lunasync, licensed under LGPLv3.

from typing import Dict, Optional, Sequence

from lunakit import Stream

from . import config, savedata


def sync(subs: Optional[Sequence[Dict[str, Optional[str]]]] = None,
         only_for_labels: Sequence[str]  = (),
         force_full:      bool           = False,
         overwrite:       bool           = False,
         warn:            bool           = True) -> int:

    downloaded = 0

    for sub in subs or config.SUBS:
        sub = {k: "" if v is None or v.strip() == "%" else v.strip()
               for k, v in sub.items()}

        if only_for_labels and \
           not any(l in only_for_labels for l in sub["labels"].split()):
            continue

        savedata.reload()

        try:
            sub_data = savedata.DATA[str(sub)]
        except KeyError:
            savedata.DATA[str(sub)] = {"last_id": 0, "success": None}
            sub_data                = savedata.DATA[str(sub)]

        stream = Stream(sub["tag_search"],
                        pages  = "all",
                        limit  = 200,
                        prefer = sub["booru"] or None).filter(sub["filter"])

        if not force_full:
            stream = stream.stop_if("id:<=%s" % sub_data["last_id"])

        passed_initial      = False
        sub_data["success"] = False

        try:
            newest_id   = sub_data["last_id"]
            newest_post = next(stream)
            newest_id   = newest_post.id

            passed_initial = True

            newest_post.write(overwrite=overwrite, warn=warn)
            stream.write(overwrite=overwrite, warn=warn)

        except StopIteration:
            if not passed_initial:
                downloaded -= 1

        except Exception:
            savedata.write()
            raise

        try:
            # Verify everything has been processed (no CTRL-C happened):
            next(stream)
        except StopIteration:
            sub_data["success"] = True
            sub_data["last_id"] = newest_id

        savedata.write()

        downloaded += stream.posts_seen
        print()

    return downloaded