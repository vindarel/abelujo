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

        total_price_discounted: (copies) ->
            sum(map ( -> it.price_discounted * it.basket_qty), copies).toFixed 2 # round a float

        total_price_excl_vat: (copies) ->
            sum(map ( -> it.price_excl_vat * it.basket_qty), copies).toFixed 2 # round a float

        total_price_discounted_excl_vat: (copies) ->
            sum(map ( -> it.price_discounted_excl_vat * it.basket_qty), copies).toFixed 2 # round a float

        total_copies: (copies) ->
            sum(map ( -> it.basket_qty), copies)

        save_quantity: (card, basket_id) !->
            """Save this card in the given basket. Card has a quantity field.
            """
            params = do
                card_id: card.id
                quantity: card.basket_qty
            $http.post "/api/baskets/#{basket_id}/update/", params
            .then (response) !->
                alerts = response.data.msgs # unused

        # next step: $resource
        distributors: ->
          $http.get "/api/distributors"

        shelfs: ->
            $http.get "/api/shelfs"

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

        getCards: (args) ->
            "Search cards, api call. Used in navbar's search, in baskets, etc.

            Use as a promise:
            >> promise = utils.getCards args
            >> promise.then (results) ->
                $scope.var = results
            "
            # repetition: that's a fail :(
            params = do
                query: args.query
                language: args.language
                with_quantity: args.with_quantity
                # card_type_id: book only ?

            cards_fetched = []

            $http.get "/api/cards/", do
                params: params
            .then (response) ->
                map !->
                  repr = "#{it.title}, #{it.authors_repr}, " + gettext("éd.") + " " + it.pubs_repr
                  it.basket_qty = 1
                  cards_fetched.push do
                      repr: repr
                      id: it.id
                      item: it
                  return do
                    repr: repr
                    id: it.id
                , response.data.cards
                return cards_fetched

        is_isbn: (text) ->
            reg = /^[0-9]{10,13}/g
            text.match reg

]
