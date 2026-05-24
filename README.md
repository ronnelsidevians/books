# PDF Library PWA — final GitHub Pages version

## Що це
PWA-застосунок для GitHub Pages. PDF-файли лежать у папці `books/`. GitHub Actions автоматично сканує папку, збирає `index.html` і деплоїть сайт.

## Головні функції
- Автоматичне розпізнавання desktop/mobile через CSS media queries.
- Mobile reader: fullscreen, без зайвих елементів, лише кнопка `×` для виходу.
- Mobile gestures: тап/свайп ліворуч і праворуч.
- Кожна PDF-сторінка ділиться на 2 частини: ліва → права → наступна сторінка.
- Обкладинка книги генерується в браузері з правої половини першої сторінки PDF.
- Прогрес читання зберігається в `localStorage` за стабільним `id` книги, додавання нових PDF не стирає прогрес.
- Плашка/статус `Прочитано`, `Читаю`, `Нова`.
- 7 тем: темна, світла, тепла, глибока мʼятна, шавлієва, блакитна, газетна.
- PWA: manifest, service worker, іконки 192/512. На iPhone встановлюється через Safari → Share → Add to Home Screen.

## Розгортання
1. Розпакуй архів у корінь репозиторію.
2. Поклади PDF у `books/`.
3. У GitHub: `Settings → Pages → Source → GitHub Actions`.
4. Commit/push.
5. Перевір зелений статус у `Actions`.
6. Відкрий сайт з `?v=final-pwa` щоб обійти кеш.

## Локально
```bash
python build_library.py --out dist --title "Моя PDF-бібліотека"
python -m http.server 8000 -d dist
```
