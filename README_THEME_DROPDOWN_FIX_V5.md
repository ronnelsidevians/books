# Theme dropdown fix v5

Виправляє проблему, коли у темних темах випадаюче меню `select` відкривалося з білим/сірим фоном і майже невидимим світлим текстом.

Змінено:

- для кожної теми додано `--dropdownBg`, `--dropdownText`, `--dropdownHover`;
- `select option` і `select optgroup` отримують фон відповідної теми;
- для `dark` і `mint` dropdown темний;
- для світлих тем dropdown світлий, але з темним читабельним текстом;
- `textarea` / коментарі також мають явний фон і колір тексту;
- кеш у `sw.js` піднято до `books-pwa-v8-mobile-ui-v5`.

Замінити у репозиторії:

- `style.css`
- `sw.js`

Після push оновити сторінку/PWA повністю, щоб service worker підтягнув новий CSS.
