do !->
   describe "the selling page ", (...) !->
       webdriver = require "selenium-webdriver"
       testUrl = "http://localhost:8000/en/sell"
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
