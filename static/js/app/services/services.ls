# Services

angular.module 'abelujo.services', [] .value 'version', '0.1'

utils = angular.module 'abelujo.services', []
utils.factory 'utils', ($http) ->

    {Obj, join, reject, sum, map, filter, find, lines} = require 'prelude-ls'

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

        export_to: (ids_qties, layout, list_name, language) ->
            """
            - ids_qties: string of coma-separated integers
            - layout: "simple": csv with isbn and quantity
                "pdf": pdf with barcodes, titles, quantity, price, and totals.
                "pdf-nobarcode"
            - list_name: str

            Return a list of alerts.
            """

            params = do
                # ids and quantities separated by comas
                "ids_qties": ids_qties
                "layout": layout
                "list_name": list_name

            $http.post "/#{language}/baskets/export/", params
            .then (response) ->
                # We get raw data. We must open it as a file with JS.
                a = document.createElement('a')
                a.target      = '_blank'
                if layout in ['simple', 'csv', 'csv_extended']
                    a.href        = 'data:attachment/csv,' +  encodeURIComponent(response.data)
                    a.download    = "#{list_name}.csv"

                else if layout in ['pdf', 'pdf-nobarcode']
                    a.href  = 'data:attachment/pdf,' +  encodeURIComponent(response.data)
                    a.download    = "#{list_name}.pdf"

                else if layout == 'txt'
                    a.href = 'data:attachment/txt,' + encodeURIComponent(response.data)
                    a.download    = "#{list_name}.txt"

                document.body.appendChild(a)
                a.click()
                []

            , (response) ->
                alerts = []
                alerts = alerts.concat do
                    level: "error"
                    message: gettext "We couldn't produce the file, there were an internal error. Sorry !"
                alerts

        # next step: $resource
        distributors: ->
          $http.get "/api/distributors"

        shelfs: ->
            $http.get "/api/shelfs"
