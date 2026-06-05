# Мінімальний патч для Books PWA v8

Замінити в корені репозиторію:

- `build_library.py`
- `app.js`
- `index.html`
- `style.css`

Після цього запустити:

```bash
python build_library.py
```

і закомітити оновлений `data/books.json` та `covers/`.

## Що змінено

- Підтримка вкладених папок у `books/**`.
- Для папки спочатку береться `icon.png`, потім `icon.jpg`, потім `icon.jpeg`.
- Якщо `icon.*` немає — лишається fallback-колаж.
- Старий `progress.json` підтримується без міграції.
- Додані необовʼязкові поля прогресу: `hidden`, `rating`, `comment`.
