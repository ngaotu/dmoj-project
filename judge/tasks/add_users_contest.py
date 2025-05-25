import csv
from tempfile import mktemp

from django.conf import settings
from django.contrib.auth.models import User

from judge.models import Profile, Contest


fields = ["username", "name", "organizations", "contest"]
descriptions = [
    "my_username(edit old one if exist)",
    "Le Van A (can be empty)",
    "cts&cts&cts&... (id contest)",
]


def csv_to_dict(csv_file):
    rows = csv.reader(csv_file.read().decode().split("\n"))
    header = next(rows)
    header = [i.lower() for i in header]

    if "username" not in header:
        return []

    res = []

    for row in rows:
        if len(row) != len(header):
            continue
        cur_dict = {i: "" for i in fields}
        for i in range(len(header)):
            if header[i] not in fields:
                continue
            cur_dict[header[i]] = row[i]
        if cur_dict["username"]:
            res.append(cur_dict)
    return res


# return result log
def import_users_to_contest(users):
    log = ""
    for i, row in enumerate(users):
        cur_log = str(i + 1) + ". "

        username = row["username"]
        cur_log += username + ": "

        user = User.objects.get(
            username=username
        )

        profile = Profile.objects.get(
            user=user
        )

        if profile.DoesNotExist:
            cur_log += "Don't have this user - Please import user"
            continue

        cur_log += "Edit - "

        if row["contest"]:
            contests = row["contest"].split("&")
            added_contests = []
            for c in contests:
                try:
                    contest = Contest.objects.get(key=c)
                    contest.private_contestants.add(profile)
                    # contest.private_contestants.set(private_contestants)
                except Contest.DoesNotExist:
                    continue
        
            if added_contests:
                cur_log += "Added to " + ", ".join(added_contests) + " - "

        # user.save()
        # profile.save()
        cur_log += "Saved\n"
        log += cur_log
    log += "FINISH"

    return log
