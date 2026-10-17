/* All content is static HTML; search, agent choice and copying are enhancements. */
const search = document.querySelector('#skill-search');
const category = document.querySelector('#skill-category');
const cards = [...document.querySelectorAll('.catalog-card')];
if (search && category) {
  document.querySelector('.catalog-filters').hidden = false;
  const filter = () => {
    const query = search.value.trim().toLocaleLowerCase();
    let count = 0;
    for (const card of cards) {
      card.hidden = !(card.textContent.toLocaleLowerCase().includes(query)
        && (!category.value || card.dataset.category === category.value));
      if (!card.hidden) count += 1;
    }
    document.querySelector('#catalog-count').textContent = `${count} of ${cards.length} skills`;
    document.querySelector('#catalog-empty').hidden = count > 0;
  };
  search.addEventListener('input', filter);
  category.addEventListener('change', filter);
  document.querySelector('#clear-filters').addEventListener('click', () => {
    search.value = '';
    category.value = '';
    filter();
    search.focus();
  });
}

const agent = document.querySelector('#install-agent');
if (agent) {
  document.querySelector('.agent-picker').hidden = false;
  const choose = () => {
    for (const section of document.querySelectorAll('[data-agent]')) {
      section.hidden = section.dataset.agent !== agent.value;
    }
  };
  agent.addEventListener('change', choose);
  choose();
}

for (const button of document.querySelectorAll('[data-copy]')) {
  button.hidden = false;
  button.addEventListener('click', async () => {
    const text = document.getElementById(button.dataset.copy);
    const status = button.closest('.command-box').querySelector('[role="status"]');
    try {
      await navigator.clipboard.writeText(text.textContent);
      status.textContent = 'Copied. Paste this command into your terminal.';
    } catch {
      text.focus();
      const range = document.createRange();
      range.selectNodeContents(text);
      const selection = window.getSelection();
      selection.removeAllRanges();
      selection.addRange(range);
      status.textContent = 'Clipboard unavailable. Text selected; copy it manually.';
    }
  });
}
