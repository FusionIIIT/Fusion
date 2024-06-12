/**
 * @fileoverview Utilities for delaying actions with WebdriverIO's
 * wdio-wait-for.
 */

var until = require('wdio-wait-for');
var DEFAULT_WAIT_TIME_MSECS = 10000;


// Wait for current url to change to a specific url.
var urlToBe = async function(url) {
  await browser.waitUntil(async function() {
    return await browser.getUrl() === url;
  },
  {
    timeout: DEFAULT_WAIT_TIME_MSECS,
    timeoutMsg: 'Url takes too long to change'
  });
};

/**
 * @param {Object} element - Clickable element such as button, link or tab.
 * @param {string} errorMessage - Error message when element is not clickable.
 */
var elementToBeClickable = async function(element, errorMessage) {
  await element.waitForClickable({
    timeout: DEFAULT_WAIT_TIME_MSECS,
    timeoutMsg: errorMessage + '\n' + new Error().stack + '\n'
  });
};

/**
 * @param {Object} element - Element expected to contain a text.
 * @param {string} text - Text value to compare to element's text.
 * @param {string} errorMessage - Error message when element does not contain
 *                                provided text.
 */
var textToBePresentInElement = async function(element, text, errorMessage) {
  await browser.waitUntil(
    await until.textToBePresentInElement(element, text),
    {
      timeout: DEFAULT_WAIT_TIME_MSECS,
      timeoutMsg: errorMessage + '\n' + new Error().stack + '\n'
    });
};

/**
 * @param {Object} element - Element is expected to be present on the DOM but
 *                           This does not mean that the element is visible.
 * @param {string} errorMessage - Error message when element is not present.
 */
var presenceOf = async function(element, errorMessage) {
  await element.waitForExist({
    timeout: DEFAULT_WAIT_TIME_MSECS,
    timeoutMsg: errorMessage + '\n' + new Error().stack + '\n'
  });
};

/**
 * @param {Object} element - Element expected to be present in the DOM and has
 *                           height and width that is greater than 0.
 * @param {string} errorMessage - Error message when element is invisible.
 */
var visibilityOf = async function(element, errorMessage) {
  await element.waitForDisplayed({
    timeout: DEFAULT_WAIT_TIME_MSECS,
    timeoutMsg: errorMessage + '\n' + new Error().stack + '\n'
  });
};

exports.urlToBe = urlToBe;
exports.elementToBeClickable = elementToBeClickable;
exports.textToBePresentInElement = textToBePresentInElement;
exports.visibilityOf = visibilityOf;
exports.presenceOf = presenceOf;