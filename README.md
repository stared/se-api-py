se-api-py
=========

A lightweight Python wrapper for [StackExchange API](http://api.stackexchange.com/) v2.1.

Build with [Requests](http://docs.python-requests.org/).

Example of ussage:

    import SEAPI
    se = SEAPI.SEAPI()
    
    se.fetch_one("users/{ids}", ids=[1,3,7,9,13], site="stackoverflow") 

    all_user = se.fetch("users", site="academia")
