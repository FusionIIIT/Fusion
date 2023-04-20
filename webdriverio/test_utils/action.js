/**
 * @fileoverview Utilities for performing actions on element in webdriverio.
 */

var waitFor = require('./waitFor.js');

var clear = async function(inputName, inputElement) {
  await click(inputName, inputElement);
  await inputElement.clearValue();
};

var click = async function(elementName, clickableElement, elementIsMasked) {
  await waitFor.visibilityOf(
    clickableElement, `${elementName} is not visible.`);
  await waitFor.elementToBeClickable(
    clickableElement, `${elementName} is not clickable.`);

  await clickableElement.click();
};

var getValue = async function(elementName, element) {
  await waitFor.presenceOf(
    element, `${elementName} is not present for getValue()`);
  return await element.getValue();
};

var getText = async function(elementName, element) {
  await waitFor.visibilityOf(
    element, `${elementName} is not visible for getText()`);
  return await element.getText();
};

// This method send a sequence of key strokes to an element after clearing
// it's value.
var setValue = async function(
    inputName, inputElement, keys, clickInputElement = true) {
  if (clickInputElement) {
    await click(inputName, inputElement);
  }
  await inputElement.setValue(keys);
};

exports.clear = clear;
exports.click = click;
exports.getText = getText;
exports.getValue = getValue;
exports.setValue = setValue;