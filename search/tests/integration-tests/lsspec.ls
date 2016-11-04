# Write protractor tests in livescript.
#
# status: broken, needs login.
#
# warning: # in livescript strings must be escaped.

do !->
    describe "the selling page ", (...) !->
        # try to login
        login = !->
            # user = element by.id "id_username"
            user = $("\#id_username")
            # pwd = element by.id "id_password"
            pwd = $("\#id_password")
            # Fails here:
            user.sendKeys "admin"
            pwd.sendKeys "admin"
            btn = $('button[type=submit]')
            btn.click!

        webdriver = require "selenium-webdriver"
        testUrl = "http://localhost:8000/en/sell"

        login!
        browser.sleep 500

        # "element" will work if we're in an angular page.
        # The following worked, but needs login.
        validateButton = element by.id "validateButton"
        input = element by.model "copy_selected"
        selectedCards = element.all by.repeater "cards_selected"

        selectCard = !->
            input.sendKeys "rue"
            browser.sleep 500
            input.sendKeys webdriver.Key.TAB

        beforeEach ->
            browser.get testUrl

        it "should display cards" !->
           selectCard()
           expect selectedCards.count! .toEqual 1
           expect browser.getTitle() .toEqual("")
