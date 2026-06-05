# Патч: вкладені папки + icon.png/icon.jpg для папок

## Що замінити у репозиторії
Скопіюй у корінь репозиторію ці файли з архіву:

- `build_library.py`
- `app.js`
- `index.html`
- `style.css`
- за бажанням `requirements.txt`

## Як тепер працює структура
Підтримуються папки будь-якої глибини:

```text
books/
  Автор/
    Серія/
      icon.png
      01 - Книга.pdf
      02 - Книга.pdf
    Інша серія/
      icon.jpg
      Книга.pdf
```

Для зображення папки використовується:

1. `icon.png` у цій папці;
2. якщо немає — `icon.jpg`;
3. якщо немає — `icon.jpeg`;
4. якщо немає жодного `icon.*` — автоматичний колаж з перших 4 обкладинок книг, як fallback.

## Після завантаження файлів
Запусти локально або через GitHub Actions:

```bash
pip install -r requirements.txt
python build_library.py
```

Потім закоміть згенеровані:

- `data/library.json`
- `covers/**`

Якщо workflow збирає у `dist`, команда також підтримується:

```bash
python build_library.py --out dist --title "PDF Library"
```
