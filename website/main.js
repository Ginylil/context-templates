/* Progressive enhancement: the full prompt remains usable without JavaScript. */
const copyButton = document.querySelector('#copy-prompt');
const promptText = document.querySelector('#install-prompt');
const copyStatus = document.querySelector('#copy-status');

if (copyButton && promptText && copyStatus) {
  copyButton.hidden = false;
  copyButton.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(promptText.textContent);
      copyStatus.textContent = 'Copied. Paste the prompt into your agent to get started.';
    } catch {
      promptText.focus();
      const selection = window.getSelection();
      const range = document.createRange();
      range.selectNodeContents(promptText);
      selection.removeAllRanges();
      selection.addRange(range);
      copyStatus.textContent = 'Clipboard unavailable. The prompt is selected; copy it manually.';
    }
  });
}
