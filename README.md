# Реализация

По примеру [статьи](https://cerfacs.fr/coop/pycallgraph).

# Запуск

```bash
pycg --package sample_app $(find tests/sample_app -type f -name "*.py") -o sample_app.json
how-it-works --graph-path sample_app.json
```
