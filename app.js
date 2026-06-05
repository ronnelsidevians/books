(() => {
  'use strict';

  const state = {
    data: null,
    path: [],
    query: '',
    theme: localStorage.getItem('books-theme') || 'light',
  };

  const $ = (id) => document.getElementById(id);
  const norm = (s) => (s || '').toString().toLowerCase().trim();

  function setTheme(theme) {
    state.theme = theme;
    localStorage.setItem('books-theme', theme);
    document.documentElement.dataset.theme = theme;
    const sel = $('themeSelect');
    if (sel) sel.value = theme;
  }

  function currentNode() {
    let node = { title: state.data.title, path: '', items: state.data.items || [] };
    for (const segment of state.path) {
      node = (node.items || []).find((x) => x.type === 'folder' && x.title === segment) || node;
    }
    return node;
  }

  function allFoldersAndBooks(items, acc = []) {
    for (const item of items || []) {
      acc.push(item);
      if (item.type === 'folder') allFoldersAndBooks(item.items, acc);
    }
    return acc;
  }

  function breadcrumb() {
    const el = $('breadcrumb');
    if (!el) return;
    el.innerHTML = '';
    const root = document.createElement('button');
    root.className = 'crumb';
    root.textContent = 'Бібліотека';
    root.onclick = () => { state.path = []; render(); };
    el.appendChild(root);
    state.path.forEach((part, idx) => {
      const sep = document.createElement('span');
      sep.className = 'sep';
      sep.textContent = '›';
      el.appendChild(sep);
      const b = document.createElement('button');
      b.className = 'crumb';
      b.textContent = part;
      b.onclick = () => { state.path = state.path.slice(0, idx + 1); render(); };
      el.appendChild(b);
    });
  }

  function itemCard(item) {
    const card = document.createElement('article');
    card.className = `card ${item.type}`;
    card.tabIndex = 0;

    const imgWrap = document.createElement('div');
    imgWrap.className = 'coverWrap';
    const img = document.createElement('img');
    img.className = 'cover';
    img.loading = 'lazy';
    img.alt = item.title || '';
    img.src = item.cover || '';
    img.onerror = () => { imgWrap.classList.add('noCover'); img.remove(); };
    imgWrap.appendChild(img);

    const meta = document.createElement('div');
    meta.className = 'meta';
    const title = document.createElement('h3');
    title.textContent = item.title || 'Без назви';
    const sub = document.createElement('p');
    if (item.type === 'folder') {
      sub.textContent = `${item.bookCount || 0} книг${item.coverSource === 'icon' ? ' · icon.*' : ''}`;
    } else {
      sub.textContent = item.folder || 'PDF';
    }
    meta.append(title, sub);

    card.append(imgWrap, meta);

    const open = () => {
      if (item.type === 'folder') {
        state.path.push(item.title);
        state.query = '';
        const input = $('searchInput');
        if (input) input.value = '';
        render();
      } else {
        openReader(item);
      }
    };
    card.onclick = open;
    card.onkeydown = (e) => {
      if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); }
    };
    return card;
  }

  function openReader(book) {
    const modal = $('reader');
    const frame = $('readerFrame');
    const title = $('readerTitle');
    const link = $('downloadLink');
    if (!modal || !frame) {
      window.open(book.file, '_blank');
      return;
    }
    title.textContent = book.title || 'PDF';
    frame.src = book.file;
    link.href = book.file;
    modal.hidden = false;
    document.body.classList.add('readerOpen');
  }

  function closeReader() {
    const modal = $('reader');
    const frame = $('readerFrame');
    if (frame) frame.src = 'about:blank';
    if (modal) modal.hidden = true;
    document.body.classList.remove('readerOpen');
  }

  function render() {
    breadcrumb();
    const grid = $('grid');
    const stats = $('stats');
    if (!grid) return;

    let items;
    if (state.query) {
      const q = norm(state.query);
      items = allFoldersAndBooks(state.data.items).filter((x) =>
        norm(x.title).includes(q) || norm(x.path).includes(q) || norm(x.folder).includes(q)
      );
    } else {
      items = currentNode().items || [];
    }

    grid.innerHTML = '';
    if (items.length === 0) {
      const empty = document.createElement('div');
      empty.className = 'empty';
      empty.textContent = state.query ? 'Нічого не знайдено' : 'У цій папці поки немає книг';
      grid.appendChild(empty);
    } else {
      for (const item of items) grid.appendChild(itemCard(item));
    }

    if (stats) {
      const folders = allFoldersAndBooks(state.data.items).filter((x) => x.type === 'folder').length;
      stats.textContent = `${state.data.totalBooks || 0} книг · ${folders} папок`;
    }
  }

  async function load() {
    setTheme(state.theme);
    try {
      const res = await fetch('data/library.json', { cache: 'no-store' });
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      state.data = await res.json();
    } catch (e) {
      console.error(e);
      state.data = { title: 'PDF Library', totalBooks: 0, items: [], flatBooks: [] };
      const err = $('error');
      if (err) {
        err.hidden = false;
        err.textContent = 'Не вдалося завантажити data/library.json. Запусти python build_library.py і закоміть data/ та covers/.';
      }
    }

    $('appTitle').textContent = state.data.title || 'PDF Library';
    $('searchInput').addEventListener('input', (e) => { state.query = e.target.value; render(); });
    $('themeSelect').addEventListener('change', (e) => setTheme(e.target.value));
    $('closeReader').addEventListener('click', closeReader);
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeReader(); });
    render();

    if ('serviceWorker' in navigator) {
      navigator.serviceWorker.register('sw.js').catch(() => {});
    }
  }

  document.addEventListener('DOMContentLoaded', load);
})();
