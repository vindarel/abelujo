# Copyright 2014 - 2019 The Abelujo Developers
# See the COPYRIGHT file at the top-level directory of this distribution

# Abelujo is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# Abelujo is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with Abelujo.  If not, see <http://www.gnu.org/licenses/>.

angular.module "abelujo" .controller 'CommandsOngoingController', ['$http', '$scope', '$window', 'utils', '$log', ($http, $scope, $window, utils, $log) !->

    {Obj, join, reject, sum, map, filter, lines, find-index} = require 'prelude-ls'

    $scope.commands = []
    $scope.alerts = []
    $scope.show_icon = {}

    $scope.language = utils.url_language($window.location.pathname)
    $scope.commands_url = "/" + $scope.language + "/commands/"
    $scope.command_popup_status = {}
    $scope.dates_labels = []

    $http.get("/api/commands/ongoing/")
    .then (response) ->
        $scope.commands = response.data
        $log.info "-- commands: ", response.data

        $scope.dates_labels =
            # 'date_sent'
            'date_received'
            'date_bill_received'
            'date_paid'
            'date_payment_sent'
        for cmd in $scope.commands
            if cmd
                for label in $scope.dates_labels
                    $scope.command_popup_status[cmd.id] = {}
                    $scope.command_popup_status[cmd.id][label] = {}
                    $scope.command_popup_status[cmd.id][label].opened = false

                    $scope.command_date[cmd.id] = {}
                    $scope.command_date[cmd.id][label] = ""
                    $scope.command_date[cmd.id][label] = cmd[label]

        return

    $scope.set_date = (cmd_id, elt, date) ->
        """Update the given date for the given command (api call). Display confirmation message.
        """
        date_formatted = date.toString($scope.date_format)
        params = do
            cmd_id: cmd_id
            date_label: elt
            date: date_formatted

        $http.post "/api/commands/#{cmd_id}/update", params
        .then (response) ->
            index = $scope.commands
            |> find-index ( -> it.id == cmd_id)

            if response.data.status == "success"  # or response.status == 200
                $scope.commands[index][elt] = date
                $scope.alerts.push do
                    level: "success"
                    message: gettext "Date changed"

            else
                $scope.alerts.concat do
                    level: "warning"
                    message: gettext "Sorry, there was an internal problem"
                $scope.alerts.concat response.data.msgs
                $scope.commands[index][elt] = undefined


    ######################################################
    # Date picker
    ######################################################
    $scope.command_date = {}  # a date for every command and date.

    $scope.today = ->
        $scope.command_date = new Date()
    $scope.today!


    $scope.command_open_datepicker = (event, cmd_id, elt) !->
        if not cmd_id or not elt
            return
        if $scope.command_popup_status[cmd_id] and not $scope.command_popup_status[cmd_id][elt]
            $scope.command_popup_status[cmd_id] = {}
            $scope.command_popup_status[cmd_id][elt] = do
                opened: true
        $scope.command_popup_status[cmd_id][elt].opened = true

    $scope.datepicker_command_options = do
        # minMode: "month"
        formatYear: 'yyyy'
        formatMonth: 'MMMM'
        startingDay: 1

    $scope.command_date_format = "ddmmyyyy" # check

    # in line with our django's date format:
    # python DATE_FORMAT = "%Y-%m-%d %H:%M:%S"
    $scope.date_format = 'yyyy-MM-dd HH:mm:ss'

    $scope.command_set_date = (cmd_id, elt) !->
        """Save the date of this command. api call.
        """
        # if not "date in future"...
        date = $scope.command_date[cmd_id][elt]
        $scope.set_date cmd_id, elt, date

    $scope.closeAlert = (index) ->
        $scope.alerts.splice index, 1

]
