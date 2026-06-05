# Патч v2

Причина, чому PDF могли перестати відкриватися: у попередньому патчі `build_library.py` записував у `data/books.json` вже percent-encoded шлях (`%D0...`), а `app.js` потім ще раз викликав `encodeURI()`. Виходило подвійне кодування (`%25D0...`) і файл не знаходився.

У v2 шляхи до PDF та `icon.png/icon.jpg/icon.jpeg` знову зберігаються сирими, як у старій логіці: `books/Папка/Книга.pdf`. `app.js` сам кодує шлях один раз при відкритті.

Замінити файли:
- `build_library.py`
- `app.js`
- `index.html`
- `style.css`

Потім запустити:

```bash
python build_library.py
```

У консолі має бути `PDF found: 237` або твоя актуальна кількість. Потім закомітити `data/books.json` і `covers/`.
