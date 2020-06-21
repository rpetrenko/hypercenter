#!/usr/bin/env python

import requests
import json
import subprocess
import sys
from faker import Factory
import os


class Kibana(object):

    def __init__(self, base_url):
        assert base_url.startswith("http")
        assert base_url[-1] != "/"
        self.base_url = base_url

    def _uri(self, path):
        assert path.startswith("/")
        return "{}{}".format(self.base_url, path)

    def _get(self, path):
        uri = self._uri(path)
        print(f"GET: {uri}")
        res = requests.get(uri)
        if res.ok:
            return res.json(), None
        else:
            return None, res

    def _post(self, path, payload=None, files=None, headers=None):
        """
        POST requests should contain kbn-xsrf header
        :param path:
        :param payload:
        :return:
        """
        _headers = {
            'Content-Type': 'application/json',
            'kbn-xsrf': 'true'
        }
        if headers is not None:
            _headers.update(headers)
        uri = self._uri(path)
        print(f"POST: {uri}")
        res = requests.post(uri, headers=_headers, json=payload, files=files)
        if res.ok:
            return res.json(), None
        else:
            print(f"ERR: {res.text}")
            return None, res.text

    def get_spaces(self):
        """

        :return: list of existing space ids
        """
        path = "/api/spaces/space"
        res, err = self._get(path)
        if not err:
            return [x['id'] for x in res]
        else:
            print(f"ERR: {err}")

    def create_space(self, space_id, **kwargs):
        """
        $ curl -X POST "localhost:5601/api/spaces/space"
            {
              "id": "marketing",
              "name": "Marketing",
              "description" : "This is the Marketing Space",
              "color": "#aabbcc",
              "initials": "MK",
              ...
            }
        :return:
        """
        path = f"/api/spaces/space"
        payload = kwargs
        payload.update({
            "id": space_id
        })
        res, err = self._post(path, payload)
        if not err:
            return res
        else:
            print(f"ERR: {err}")

    def get_index_pattern(self, space_id=None, title=""):
        if space_id is not None:
            path = f"/s/{space_id}/api/saved_objects/_find?type=index-pattern&search_fields=title&search={title}"
        else:
            path = f"/api/saved_objects/_find?type=index-pattern&search_fields=title&search={title}"
        res, err = self._get(path)
        if not err:
            return res['saved_objects']
        else:
            print(f"ERR: {err}")

    def _insert_space(self, path, space_id):
        if space_id:
            path = f"/s/{space_id}{path}"
        return path

    def create_index_pattern(self, space_id=None, attributes=None):
        obj_type = "index-pattern"
        path = self._insert_space(f"/api/saved_objects/{obj_type}", space_id)

        payload = {
            "attributes": attributes
        }
        res, err = self._post(path, payload=payload)
        if not err:
            return res
        else:
            print(f"ERR: {err}")

    def import_saved_objects(self, fname, space_id=None):
        """
        curl -X POST "localhost:5601/s/automation/api/saved_objects/_import" -H "kbn-xsrf: true" --form file=@file.ndjson
        :param fname:
        :param space_id:
        :return:
        """
        space_line = f"/s/{space_id}" if space_id else ""
        cmd = ['curl', '-s', '-X', 'POST', f"http://localhost:5601{space_line}/api/saved_objects/_import", '-H', "kbn-xsrf: true", '--form', f'file=@{fname}']
        print(" ".join(cmd))
        out = subprocess.check_output(cmd)
        out = json.loads(out)
        res = out['success']
        if res:
            return res, None
        else:
            return None, out['errors']

    def import_dashboard(self, fname, space_id=None):
        """
        curl -X POST "localhost:5601/api/kibana/dashboards/import?exclude=index-pattern"
        :param fname:
        :return:
        """
        path = "/api/kibana/dashboards/import"
        path = self._insert_space(path, space_id)
        payload = json.load(open(fname, 'r'))
        res, err = self._post(path, payload=payload)
        if res:
            return res, None
        else:
            return None, res


def create_automation_space(kib, space_id, **kwargs):
    if space_id not in kib.get_spaces():
        _kwargs = {
            "name": space_id.title(),
            "color": "#aabbcc",
            "initials": space_id[:2].upper(),
        }
        _kwargs.update(kwargs)
        kib.create_space(space_id, **_kwargs)


def create_index_patterns(kib, space_id, index_patterns):
    """

    :param kib:
    :param space_id:
    :param index_patterns: list of index patterns, like: test*, or hypermanager
    :return:
    """
    for pattern in index_patterns:
        if kib.get_index_pattern(space_id=space_id, title=pattern):
            print("Skip, already exists")
        else:
            res = kib.create_index_pattern(
                space_id=space_id,
                attributes={"title": pattern}
            )
            print(res)


def import_saved_objects(kib, fname, space_id=None):
    res, err = kib.import_saved_objects(fname, space_id=space_id)
    if not res:
        print(f"ERR: {err}")
    return res


def import_dashboards(kib, fname, space_id=None):
    res, err = kib.import_dashboard(fname, space_id=space_id)
    print(res)


if __name__ == "__main__":
    """
    Usage:
        python setup.py <space_id> <json file for dashboard import>
    Example:
        python setup.py test dashboards

    """

    space_id = sys.argv[1]
    exports_dir = sys.argv[2]

    base_url = "http://localhost:5601"
    kib = Kibana(base_url)

    # create automation space
    kwargs = {
        "description": "Created by automation",
        "color": Factory.create().hex_color()
    }
    create_automation_space(kib, space_id, **kwargs)
    for fname in os.listdir(exports_dir):
        fname = os.path.join(exports_dir, fname)
        print(fname)
        import_dashboards(kib, fname, space_id=space_id)