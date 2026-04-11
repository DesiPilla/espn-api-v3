// jest-dom adds custom jest matchers for asserting on DOM nodes.
// allows you to do things like:
// expect(element).toHaveTextContent(/react/i)
// learn more: https://github.com/testing-library/jest-dom
import '@testing-library/jest-dom';

// @testing-library/dom v10 uses MutationObserver inside waitFor().
// CRA 5's jest 27 + jsdom 16 environment doesn't expose it as a global
// constructor, so we polyfill it here.  waitFor still works via its
// interval-based polling even when the observer never fires.
if (typeof global.MutationObserver === 'undefined') {
  global.MutationObserver = class MutationObserver {
    constructor(callback) {}
    disconnect() {}
    observe() {}
    takeRecords() { return []; }
  };
}
