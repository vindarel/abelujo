# Services

angular.module 'abelujo.services', [] .value 'version', '0.1'

utils = angular.module 'abelujo.services', []
utils.factory 'utils', ->
    do
        # We need not to pass the parameters encoded as json to Django,
        # because it re-encodes everything in json and the result is horrible.
        # Encode them like url parameters.

        transformRequestAsFormPost: (obj) ->
            # obj: with simple types, not dicts
            str = []
            for p of obj
                str.push encodeURIComponent(p) + "=" + encodeURIComponent obj[p]
            str.join("&")

        url_language: (url) ->
            re = /\/([a-z][a-z])\//
            res = url.match(re)
            if res
                return res[1]
            "en"
