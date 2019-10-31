#!/usr/bin/env python3

import itertools
from packaging import version
import requests
import re
import yaml
import pprint
import os

RELS = {
    "kubectl": {"1.13": ["v1.13.10"]}
}

def candidates(key: str, releases: list, match: list):
    pattern = re.compile(match)

    RELS.setdefault(key, [])

    data = {}
    for release in releases:
        k = str(release["tag_name"])

        ver = version.parse(k)
        series = ver.base_version[0:3]

        data.setdefault(series, [])
        match = pattern.match(k)
        if match is not None:
            data[series].append((k, ver))
    
    # Sort and select out latest 3 releases
    for ver, items in data.items():
        items.sort(key=lambda i: i[1])
        latest = items[-3:]
        candidates = list(map(lambda i: i[0], latest))

        data[ver] = candidates

        print("Latest %s" % list(candidates))

    RELS[key] = data


def fetch_releases(repo):
    user = os.environ.get("GITHUB_USER")
    token = os.environ.get("GITHUB_TOKEN")

    auth = None
    if user and token:
        auth=(user, token)

    response = requests.get(
        "https://api.github.com/repos/%s/releases" % repo, 
        auth=auth)

    return response.json()


if __name__ == '__main__':
    helm_rels = fetch_releases("helm/helm")
    candidates("helm", helm_rels, "(v2.15|v3.\d+\.\d+(|-rc.\d)$)")

    terraform_rels = fetch_releases("hashicorp/terraform")
    candidates("terraform", terraform_rels, "v0.12.\d+$")

    data = []
    for t in ["helm", "kubectl", "terraform"]:
        series = RELS[t]
        releases = list(series.values())[0]
        data.append(releases)

    candidate_tuples = list(itertools.product(*data))

    for candidate in candidate_tuples:
        print(" ".join(candidate))

        data = {
            "helm-version": candidate[0],
            "kubectl-version": candidate[1],
            "tf-version": candidate[2][1:],
        }
        # print (data)
        requests.post("http://el-docker-helm-kubectl-terraform-listener:8080", json=data)

# print(candidates)

# print(releases.keys())