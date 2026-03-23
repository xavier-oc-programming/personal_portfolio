/* api-docs.js
 *
 * Powers the "Try it" widgets on the API documentation page.
 * Each widget has a URL input, a Run button, and a collapsible output block.
 */

(function () {
  'use strict';

  // Clicking an example button loads its URL into the widget's input and runs it
  document.addEventListener('click', function (e) {
    const exBtn = e.target.closest('.api-try-example');
    if (exBtn) {
      const widget = exBtn.closest('.api-try-it');
      const input  = widget.querySelector('.api-try-url');
      if (input) {
        input.value = exBtn.dataset.url;
      }
    }
  });

  document.addEventListener('click', async function (e) {
    const btn = e.target.closest('.api-try-run');
    if (!btn) return;

    const widget = btn.closest('.api-try-it');
    const input = widget.querySelector('.api-try-url');
    const output = widget.querySelector('.api-try-output');
    const code = output.querySelector('code');

    const url = (input.value || '').trim();
    if (!url) return;

    btn.disabled = true;
    btn.textContent = 'Loading…';
    output.classList.remove('d-none');
    code.textContent = 'Fetching…';

    try {
      const res = await fetch(url);
      const json = await res.json();
      code.textContent = JSON.stringify(json, null, 2);
    } catch (err) {
      code.textContent = `Error: ${err.message}`;
    } finally {
      btn.disabled = false;
      btn.textContent = 'Run';
    }
  });

}());
