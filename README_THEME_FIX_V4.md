# Theme visibility fix v4

Виправляє проблему зі скріншота: у темній/мʼятній темі текст пунктів `select` був світлий на білому фоні системного dropdown, тому оцінки було майже не видно.

Що змінено в `style.css`:

- додано `color-scheme` для тем;
- задано контрастні кольори для `select option` / `optgroup`;
- задано явні кольори для `textarea` / `.commentBox`, placeholder і caret;
- додано focus-visible outline;
- залишено стилі для зірочок, коментарів, прихованих карток і reader error.

Також у `sw.js` піднято версію кешу до `books-pwa-v8-mobile-ui-v4`, щоб браузер не тримав старий CSS.

Замінити:

- `style.css`
- `sw.js`

Після push бажано повністю оновити сторінку/PWA.
