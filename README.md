se-api-py
=========

A lightweight Python wrapper for [StackExchange API](http://api.stackexchange.com/) v2.1.
Build with [Requests](http://docs.python-requests.org/).

It uses:
	* se.fetch[_one](command, **parameters)
	* parameters as in the documentation
	* in the command, "{something}" and "{somethings}" are treated as placeholders for an int/str or a list of int/str, respectively

Example of usage:

    import SEAPI
    se = SEAPI.SEAPI()
    
    some_users = se.fetch_one("users/{ids}", ids=[1,3,7,9,13], site="stackoverflow") 

    all_user = se.fetch("users", site="academia")


Alternatively, you can initialize SEAPI with default options, typically - site name, e.g.

	so = SEAPI.SEAPI(site="stackoverflow")

	some_questions = so.fetch("questions", page_limit=10)
	# except for very small sites, you want to set page limit

	some_sorted_posts = so.fetch_one("posts", order="desc", sort="votes")
	# for sorting sometimes asking for more that one results in "throttle violation"

If you want to diagnose a problem, or avoid it:

	so.last_call
	# lookup at the last command sent

	so.last_status
	# check the last response status

	slow_food = so.fetch("tags", min_delay=0.5)
	# or set delay (by default it's 0.05)