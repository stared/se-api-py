import requests
try:
    import simplejson as json
except:
    import json

class SEAPI():
    def __init__(self):
        # also allow setting default command or default parameters?
        self.default_params = {"pagesize":100}

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

    def _replace_placeholders(self, command, **kwargs):
        """Parses API command to find placeholders
           for elements '{foo}' or lists '{foos}',
           replacing them with kwargs foo=number, or foos=list;
           EXAMPLE:
           >>> seapi._replace_placeholders("users/{ids}/comments/{toid}",
                                     ids = [1, 2], toid = 5)
           "users/1;2/comments/5"  """
        parts = command.split("/")
        for i, part in enumerate(parts):
            if part.startswith("{"):
                if part.endswith("s}"):
                    parts[i] = ";".join(map(str, kwargs[part[1:-1]]))
                elif part.endswith("}"):
                    parts[i] = str(kwargs[part[1:-1]])
        return "/".join(parts)


    def fetch_one(self, command, **kwargs):
        """Returns one page of results for a given command;
        EXAMPLE:
        >>> seapi.fetch_one("users/{ids}", ids=[1,3,7,9,13], site=stackoverflow) 
        >>> seapi.fetch_one("posts", order=desc, sort=votes, site=stackoverflow, page=3)"""
        url = "%s/%s/%s" % (self.api_address, self.api_version,
            self._replace_placeholders(command, **kwargs))
        parameters = self.default_params.copy()
        parameters.update(kwargs)
        # to fix: in params there unintentionally thinga like ids = [1,2,3]

        r = requests.get(url, params = parameters)
        data = json.loads(r.content)

        self.last_call = [url, parameters]
        self.last_status = dict([(k, data[k]) for k in data if k != 'items'])

        return data['items']
    

    def fetch(self, command, starting_page = 1, page_limit = 1000, print_progress = True, **kwargs):
        """Returns all pages (withing the limit) of results for a given command;
        EXAMPLE -> check for fetch_one (without 'page' parameter!)
        NOTE: Here is a lot of room for improvements and additional features, e.g.:
        - separating also by large {ids} lists
        - gevent for concurrency
        - measuring time per response and keeping it optimal (not to get banned),
        - check page limit?"""
        res = []
        if print_progress:
            print "Fetching pages: ",
        for i in xrange(starting_page, starting_page + page_limit):
            if print_progress:
                print i,
            res += self.fetch_one(command, page = i, **kwargs)
            if not self.last_status['has_more']:
                break
        return res

