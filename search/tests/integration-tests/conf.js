// conf.js
// full list of capabilities: https://github.com/angular/protractor/blob/master/docs/referenceConf.js
// selenium capabilities: https://github.com/SeleniumHQ/selenium/wiki/DesiredCapabilities
exports.config = {
  seleniumAddress: 'http://localhost:4444/wd/hub',
  specs: ['spec.js'],

  capabilities: {
    // phantomJS isn't adviced.
    browserName: 'firefox'
  }
}
