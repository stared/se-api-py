import requests
try:
    import simplejson as json
except:
    import json
from time import time, sleep


class SEAPI():
    def __init__(self, **kwargs):
        """Use kwargs to set default parameters, e.g.
        >>> se = SEAPI(site="stackoverflow")"""
        self.default_params = {"pagesize": 100}  # explicit "pagesize" is required
        self.default_params.update(kwargs)

        self.api_address = "http://api.stackexchange.com"
        self.api_version = "2.1"
        self.key = "o*kk9*eL4o0QSbBWTpIf3A(("
        self.access_token = ""

        if self.key:
            self.default_params['key'] = self.key
        if self.access_token:
            self.default_params['access_token'] = self.access_token

        self.last_call = ["", {}]
        self.last_status = {}
        self.last_response_times = []

    # def _replace_placeholders(self, command, **kwargs):
    #     """Parses API command to find placeholders
    #        for elements '{foo}' or lists '{foos}',
    #        replacing them with kwargs foo=number, or foos=list;
    #        EXAMPLE:
    #        >>> seapi._replace_placeholders("users/{ids}/comments/{toid}",
    #                                  ids = [1, 2], toid = 5)
    #        "users/1;2/comments/5"  """
    #     parts = command.split("/")
    #     for i, part in enumerate(parts):
    #         if part.startswith("{"):
    #             if part.endswith("s}"):
    #                 parts[i] = ";".join(map(str, kwargs[part[1:-1]]))
    #             elif part.endswith("}"):
    #                 parts[i] = str(kwargs[part[1:-1]])
    #     return "/".join(parts)

    def _find_placeholders(self, raw_command, **kwargs):
        parts = raw_command.split("/")
        curly_params = {}   # e.g. for "{id}"
        curly_list_params = {}  # e.g. for "{ids}"; and dict with max 1 element
        for part in parts:
            if part.startswith("{"):
                if part.endswith("s}"):
                    curly_list_params[part[1:-1]] = kwargs[part[1:-1]]
                elif part.endswith("}"):
                    curly_params[part[1:-1]] = kwargs[part[1:-1]]
        return (parts, curly_params, curly_list_params)

    def _combine_placeholders(self, parts, curly_params, curly_list_params):
        parts_filled = parts[:]
        for i, part in enumerate(parts_filled):
            if part.startswith("{"):
                if part.endswith("s}"):
                    parts_filled[i] = ";".join(map(str, curly_list_params[part[1:-1]]))
                elif part.endswith("}"):
                    parts_filled[i] = str(curly_params[part[1:-1]])
        return "/".join(parts_filled)

    def _chunks(self, li, k):
        """Splits a list in list of k elements, e.g.
        >>> split([2, 3, 5, 7, 11, 13, 17, 19], 3)
        [[2, 3, 5], [7, 11, 13], [17, 19]]"""
        return [li[i:(i + k)] for i in xrange(0, len(li), k)]

    def fetch_one(self, command, subcommand=False, parse_curly_parameters=True, **kwargs):
        """Returns one page of results for a given command;
        EXAMPLE:
        >>> seapi.fetch_one("users/{ids}", ids=[1,3,7,9,13], site=stackoverflow)
        >>> seapi.fetch_one("posts", order=desc, sort=votes, site=stackoverflow, page=3)"""

        parameters = self.default_params.copy()

        if parse_curly_parameters:
            parts, curly_params, curly_list_params = self._find_placeholders(command, **kwargs)
            command = self._combine_placeholders(parts, curly_params, curly_list_params)
            parameters.update(
                dict([(k, v) for k, v in kwargs.items()
                if (k not in curly_params) and (k not in curly_list_params)])
                )
        else:
            parameters.update(kwargs)

        url = "%s/%s/%s" % (self.api_address, self.api_version, command)

        t0 = time()
        r = requests.get(url, params=parameters)
        if not subcommand:
            self.last_response_times = []
        self.last_response_times.append(time() - t0)

        data = json.loads(r.content)

        self.last_call = [url, parameters]
        self.last_status = dict([(k, data[k]) for k in data if k != 'items'])

        return data['items']

    def fetch(self, command, starting_page=1, page_limit=2000, print_progress=True, min_delay=0.05, **kwargs):
        """Returns all pages (withing the limit) of results for a given command;
        autimatically splits lists for {ids} in approperiate chunks
        EXAMPLE -> check for fetch_one (without 'page' parameter!)
        NOTE: Here is a lot of room for improvements and additional features, e.g.:
        - gevent for concurrency to get optimal rate
        - dealing with 'Violation of backoff parameter' """
        res = []
        self.last_response_times = []
        parts, curly_params, curly_list_params = self._find_placeholders(command, **kwargs)

        parameters = self.default_params.copy()
        parameters.update(
            dict([(k, v) for k, v in kwargs.items()
            if (k not in curly_params) and (k not in curly_list_params)])
            )

        if curly_list_params:
            assert(len(curly_list_params) == 1)
            curly_name, curly_list = curly_list_params.items()[0]
            pieces = self._chunks(curly_list, parameters['pagesize'])
            for piece in pieces:
                command = self._combine_placeholders(parts, curly_params, {curly_name: piece})
                res += self.fetch_one(command, subcommand=True, parse_curly_parameters=False, **parameters)
                # ^ maybe also with try/except/once_again?
                if self.last_response_times[-1] < min_delay:
                        sleep(min_delay - self.last_response_times[-1])
                        if print_progress:
                            print "waited %.2f" % (min_delay - self.last_response_times[-1])
        else:
            command = self._combine_placeholders(parts, curly_params, {})
            if print_progress:
                print "Fetching pages: ",
            for i in xrange(starting_page, starting_page + page_limit):
                if print_progress:
                    print i,
                try:
                    res += self.fetch_one(command, subcommand=True, parse_curly_parameters=False, page=i, **parameters)
                except:
                    print self.last_status
                    print "waiting 60s and trying once more"  # mainly for 'Violation of backoff parameter'
                    sleep(60.)
                    res += self.fetch_one(command, subcommand=True, parse_curly_parameters=False, page=i, **parameters)
                if not self.last_status['has_more']:
                    break
                if self.last_response_times[-1] < min_delay:
                    sleep(min_delay - self.last_response_times[-1])
                    if print_progress:
                        print "waited %.2f" % (min_delay - self.last_response_times[-1])

        return res

    def status_of(self, command, **kwargs):
        self.fetch_one(command, **kwargs)
        return self.last_status
