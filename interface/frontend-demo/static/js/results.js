(function () {
  const container = document.getElementById('results-container');
  const template = document.getElementById('result-template');
  const emptyTemplate = document.getElementById('results-empty-template');
  let result;
  try { result = JSON.parse(sessionStorage.getItem('hashCrackerLastResult')); } catch (_) { result = null; }
  if (!result || typeof result !== 'object') {
    container.appendChild(emptyTemplate.content.cloneNode(true));
  } else {
    const node = template.content.cloneNode(true);
    const state = node.querySelector('[data-field="state"]');
    const stamp = node.querySelector('[data-field="stamp"]');
    const description = node.querySelector('[data-field="description"]');
    const statuses = {
      found: ['FOUND', 'CRACKED!', 'The backend found a matching value.'],
      not_found: ['NOT FOUND', 'NO MATCH', 'No matching value was found in the backend wordlist.'],
      processing: ['PROCESSING', 'IN PROGRESS', 'The backend reports that this request is still processing.'],
      error: ['ERROR', 'ERROR', 'The backend could not complete this request.']
    };
    const labels = statuses[result.status] || ['UNKNOWN', 'UNKNOWN', 'The backend returned an unrecognized status.'];
    state.textContent = labels[0];
    state.classList.add(result.status === 'not_found' ? 'not-found' : (Object.hasOwn(statuses, result.status) ? result.status : 'unknown'));
    stamp.textContent = labels[1];
    description.textContent = labels[2];
    node.querySelector('[data-field="hash"]').textContent = result.hash || 'Not reported';
    const algorithm = AlgorithmConfig.byId(result.algorithm);
    node.querySelector('[data-field="algorithm"]').textContent = algorithm ? algorithm.label : (result.algorithm || 'Not reported');
    const password = typeof result.password === 'string' ? result.password : null;
    // A running Flask server may still have the previous template cached after an update.
    // Upgrade its result field in place so mixed template/script versions remain usable.
    let resultLabel = node.querySelector('[data-field="result-label"]');
    if (!resultLabel) {
      const passwordField = node.querySelector('[data-field="password"]');
      const oldField = passwordField.closest('.result-field');
      if (oldField) {
        oldField.className = 'result-highlight';
        resultLabel = oldField.querySelector('.field-label');
        if (resultLabel) resultLabel.className = 'result-highlight-label';
        const content = document.createElement('div');
        content.className = 'result-highlight-content';
        const copyButton = oldField.querySelector('[data-field="copy"]');
        content.appendChild(passwordField);
        if (copyButton) content.appendChild(copyButton);
        oldField.insertBefore(content, oldField.querySelector('[data-field="copy-message"]'));
        const resultStamp = node.querySelector('[data-field="stamp"]');
        if (resultStamp) resultStamp.after(oldField);
      }
    }
    if (resultLabel) resultLabel.textContent = result.status === 'found' ? 'RECOVERED PASSWORD' : 'RESULT';
    node.querySelector('[data-field="password"]').textContent = result.status === 'found' && password !== null ? password : result.status === 'not_found' ? 'Not found' : result.status === 'processing' ? 'Processing' : 'Not available';
    node.querySelector('[data-field="duration"]').textContent = Number.isFinite(result.durationMs) ? `${result.durationMs} ms` : 'Not reported';
    const copy = node.querySelector('[data-field="copy"]');
    const message = node.querySelector('[data-field="copy-message"]');
    if (result.status === 'found' && password !== null) {
      copy.hidden = false;
      copy.addEventListener('click', async () => {
        try {
          if (!navigator.clipboard || !navigator.clipboard.writeText) throw new Error('Clipboard unavailable');
          await navigator.clipboard.writeText(password);
          message.textContent = 'Copied!';
        } catch (_) { message.textContent = 'Could not copy. Select the value to copy it.'; }
      });
    }
    container.appendChild(node);
  }
  if (ApiMode.current === 'mock') container.querySelectorAll('a[href]').forEach(link => {
    const url = new URL(link.href, location.href);
    if (url.origin === location.origin) { url.searchParams.set('mode', 'mock'); link.href = url.href; }
  });
})();
