# Services

angular.module 'abelujo.services', [] .value 'version', '0.1'

utils = angular.module 'abelujo.services', []
utils.factory 'utils', ->
    do
        # We need not to pass the parameters encoded as json to Django,
        # because it re-encodes everything in json and the result is horrible.
        # Encode them like url parameters.

        transformRequestAsFormPost: (obj) ->
            # obj: a list of simple types, not dicts
            str = []
            for p of obj #of / in breaking inventory or ok ? TODO:
                str.push encodeURIComponent(p) + "=" + encodeURIComponent obj[p]
            str.join("&")
