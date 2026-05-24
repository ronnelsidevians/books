# Workflow fix

Помилка була тут:

```text
cp: cannot stat '.nojekyll': No such file or directory
```

У цьому workflow файл `.nojekyll` створюється напряму в `dist` командою:

```bash
touch dist/.nojekyll
```

Замініть `.github/workflows/pages.yml` на файл з цього архіву.
