# Запуск

```bash
how-it-works --root tests --entry-point sample_app/cli.py > calls.dot
dot -Tsvg calls.dot > calls.svg
```
