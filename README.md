# ДЗ 1 · Мини-трекер учебных задач: прямой промпт и спецификация

## О задании
Один и тот же мини-трекер учебных задач на неделю сделан двумя способами. Результаты сравниваются по общим проверкам T1–T5.

- **direct / v1** — один прямой промпт: «сделай трекер». Результат: `tracker-v1.html`. По итогам ручной проверки в нём найден баг с часами: не соблюдаются шаг 0,5 и границы 0,5–24. Исправленная версия лежит отдельно в `tracker-v1-corrected.html`.
- **spec / v2** — сначала спецификация в формате OpenSpec (`proposal.md`, `specs/tracker/spec.md`, `design.md`, `tasks.md`), затем реализация по ней. Результат: `tracker-v2.html`.

Модель: Claude Opus 5.5, 14.11.2026. Итоги, таблица проверок и выводы — в `report.md`, тексты всех промптов — в `prompts.txt`.

## Состав папки
```
ИИ_дз1/
├── README.md                  — этот файл
├── report.md                  — отчёт и таблица T1–T5
├── prompts.txt                — тексты всех промптов
├── tracker-v1.html            — v1, прямой промпт (исходник, не изменялся)
├── tracker-v1-corrected.html  — v1 с исправленной проверкой часов
├── tracker-v2.html            — v2, реализация по спецификации
├── proposal.md                — OpenSpec: цель и границы
├── design.md                  — OpenSpec: данные и расчёты
├── tasks.md                   — OpenSpec: чек-лист реализации и проверок
├── specs/tracker/spec.md      — OpenSpec: требования MUST и сценарии WHEN/THEN
└── tests/
    ├── run_t1_t5.py           — автопроверка T1–T5 для трёх трекеров
    ├── run_tracker_checks.py  — автопроверка 6.1–6.12 из tasks.md для v2
    └── screenshot-390px.png   — снимок v2 на ширине 390 px
```

## Запуск трекеров
Ничего устанавливать не нужно, сервер не требуется.

1. Откройте папку `ИИ_дз1` в Finder.
2. Дважды щёлкните `tracker-v2.html`, `tracker-v1.html` или `tracker-v1-corrected.html`. Файл откроется в браузере по умолчанию.
3. Для проверки на телефонной ширине откройте инструменты разработчика (Chrome: ⌥⌘I → значок устройства) и задайте ширину 390 px.

v1 и v1-corrected сохраняют задачи в браузере. Чтобы начать со стартового примера, нажмите «Вернуть пример». v2 при каждом открытии начинает со стартового примера.

## Запуск автопроверок (необязательно)
Нужны Python 3 и Playwright:

```
pip install playwright
playwright install chromium
cd ~/ИИ_дз1
python3 tests/run_t1_t5.py .
python3 tests/run_tracker_checks.py tracker-v2.html
```

Чтобы использовать установленный Chrome вместо скачанного Chromium, добавьте перед командой:
`CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"`.

## Проверка спецификации (необязательно)
Если установлен OpenSpec CLI, разложите документы в `openspec/changes/add-weekly-study-tracker/` и выполните `openspec validate add-weekly-study-tracker`. В рамках ДЗ валидатор не запускался.
