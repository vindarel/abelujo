(function(){
    describe("The selling page", function() {
        var webdriver, testUrl, validateButton, input, selectedCards;
        webdriver = require("selenium-webdriver");
        // Requires: testing data (make data),
        // starting selenium (make wedriver-manager).
        testUrl = "http://localhost:8000/en/sell";
        validateButton = element(by.id("validateButton"));
        input = element(by.model("copy_selected"));
        selectedCards = element.all(by.repeater("cards_selected"));
        function selectCard() {
            input.sendKeys("rue");
            // Isn't protractor supposed to wait the result of a $http call ?
            browser.sleep(500);
            input.sendKeys(webdriver.Key.TAB);
        }

        beforeEach(function() {
            browser.get(testUrl);
        });

        it("should display cards of the autocomplete.", function() {
            selectCard();
            expect(selectedCards.count()).toEqual(1);
            expect(browser.getTitle()).toEqual("");
        });
    });
})();
