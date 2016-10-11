# Services

angular.module 'abelujo.services', [] .value 'version', '0.1'

utils = angular.module 'abelujo.services', []
utils.factory 'utils', ['$http', '$log', ($http, $log) ->

    {Obj, join, reject, sum, map, filter, find, lines, sort-by, reverse, take, unique-by, mean, id, each} = require 'prelude-ls'

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
            # extract the language from an url like /fr/foo/bar
            re = /\/([a-z][a-z])\//
            res = url.match(re)
            if res
                return res[1]
            "en"

        locale_language: (str) ->
            """Take a short string specifying a language (exple: fr,
            es; taken from the url) and return one that has meaning
            for angular's $locale.
            """
            if str == "fr"
                return "fr-fr"
            if str == "es"
                return "es-es"
            if str == "de"
                return "de-de"
            "en-gb"

        url_id: (url) ->
            # extract an id
            re = /\/(\d+)/
            res = url.match(re)
            if res and res.length == 2
                return res[1]
            null

        set_focus: !->
            angular.element('#default-input').trigger('focus');

        total_price: (copies) ->
            sum(map ( -> it.price * it.basket_qty), copies).toFixed 2 # round a float

        total_copies: (copies) ->
            sum(map ( -> it.basket_qty), copies)

        save_quantity: (card, basket_id) !->
            params = do
                id_qty: "#{card.id},#{card.basket_qty}"
            $http.post "/api/baskets/#{basket_id}/update/", params
            .then (response) !->
                alerts = response.data.msgs # unused

        # next step: $resource
        distributors: ->
          $http.get "/api/distributors"

        shelfs: ->
            $http.get "/api/shelfs"

        sells_total_sold: (sells) ->
            """
            - sells: list of objects, with a card_id and a quantity
            - return: the sells with a new property, total_sold
            """
            for sell in sells
                sell.total_sold = sells
                |> filter (.card_id == sell.card_id)
                |> map (.quantity)
                |> sum

            sells

        best_sells: (sells) ->
            """
            - sells: list of objects, with a .total_sold (see function above)
            - return: the 10 best sells
            """
            best_sells = sells
            |> unique-by (.card_id)
            |> sort-by (.total_sold)
            |> reverse
            |> take 10

            best_sells

        sells_mean: (sells) ->
            """
            - return the global mean of sells operation: how much in a sell by average.
            """
            for sell in sells
                sell.total_sell = sells
                |> filter (.sell_id == sell.sell_id)
                |> map ( -> it.price_sold * it.quantity)
                |> mean

            sells
            |> unique-by (.sell_id)
            |> map (.total_sell)
            |> mean

]
