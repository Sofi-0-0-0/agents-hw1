"""Автотест tracker-v2.html по проверкам 6.1–6.12 из tasks.md.

Установка:  pip install playwright && playwright install chromium
Запуск из папки ИИ_дз1:  python3 tests/run_tracker_checks.py tracker-v2.html
Свой Chrome вместо скачанного Chromium:  CHROME_PATH=/путь/к/chrome python3 tests/run_tracker_checks.py tracker-v2.html
"""
import os, re, sys, pathlib
from playwright.sync_api import sync_playwright

path = pathlib.Path(sys.argv[1]).resolve()
src = path.read_text(encoding='utf-8')
results = []
def check(name, cond, detail=''):
    results.append((name, bool(cond), detail))

# 6.1 static scan
pats = [r'https?://', r'//cdn', r'<script[^>]*\bsrc=', r'<link\b', r'@import', r'\bfetch\s*\(', r'XMLHttpRequest', r'localStorage']
for p in pats:
    m = re.search(p, src, re.I)
    check(f'6.1 нет {p}', m is None, m.group(0) if m else '')

with sync_playwright() as pw:
    chrome = os.environ.get('CHROME_PATH')
    b = pw.chromium.launch(executable_path=chrome) if chrome else pw.chromium.launch()
    ctx = b.new_context(viewport={'width': 390, 'height': 844}, locale='ru-RU', offline=True)
    page = ctx.new_page()
    reqs, errors = [], []
    page.on('request', lambda r: reqs.append(r.url))
    page.on('pageerror', lambda e: errors.append(str(e)))
    page.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
    url = path.as_uri()

    def summary():
        return (page.text_content('#total-hours'), page.text_content('#done-hours'), page.text_content('#progress'))
    def titles():
        return page.eval_on_selector_all('.task-title', 'els => els.map(e => e.textContent)')
    def fresh():
        page.goto(url); 
    def add(t, h):
        page.fill('#title-input', t); page.fill('#hours-input', h); page.click('button[type=submit]')
    def toggle(name):
        page.get_by_role('checkbox', name=name, exact=True).click()
    def delete(name):
        page.get_by_role('button', name=f'Удалить «{name}»').click()
    def state_titles():
        return page.evaluate('state.tasks.map(t => t.title + ":" + t.hours + ":" + t.done)')

    # 6.3
    fresh()
    check('6.3 старт: 3 задачи', titles() == ['Чтение','Практика','Повторение'], titles())
    check('6.3 старт: 8 ч / 2 ч / 25%', summary() == ('8 ч','2 ч','25%'), summary())
    # 6.4
    toggle('Практика')
    check('6.4 Практика готова: 8/6/75%', summary() == ('8 ч','6 ч','75%'), summary())
    check('6.4 done=true в данных', 'Практика:4:true' in state_titles(), state_titles())
    # 6.5
    fresh()
    page.get_by_role('radio', name='Активные').check()
    check('6.5 Активные: список', titles() == ['Практика','Повторение'], titles())
    check('6.5 Активные: 25%', summary() == ('8 ч','2 ч','25%'), summary())
    toggle('Практика')
    check('6.5 Активные + Практика готова: скрыта', titles() == ['Повторение'], titles())
    check('6.5 Активные + Практика готова: 75%', summary()[2] == '75%', summary())
    page.get_by_role('radio', name='Все').check()
    check('6.5 Все: снова все', titles() == ['Чтение','Практика','Повторение'], titles())
    # 6.6
    for t in ['', '    ']:
        fresh(); add(t, '2')
        err = page.locator('#title-error')
        check(f'6.6 название {t!r}: не добавлено', len(titles()) == 3)
        check(f'6.6 название {t!r}: ошибка видна', err.is_visible() and err.text_content() == 'Введите название', err.text_content())
        check(f'6.6 название {t!r}: часы сохранены', page.input_value('#hours-input') == '2')
    # 6.7
    cases = {'': 'Укажите часы', '   ': 'Укажите часы', '-1': 'Допустимо от 0,5 до 24 ч', '0': 'Допустимо от 0,5 до 24 ч',
             '25': 'Допустимо от 0,5 до 24 ч', '0,75': 'Шаг — 0,5 ч', 'abc': 'Введите число, например 1,5', '30': 'Допустимо от 0,5 до 24 ч'}
    for h, msg in cases.items():
        fresh(); add('Практика 2', h)
        err = page.locator('#hours-error')
        ok = (len(titles()) == 3 and err.is_visible() and err.text_content() == msg
              and page.input_value('#title-input') == 'Практика 2' and page.input_value('#hours-input') == h
              and summary() == ('8 ч','2 ч','25%')
              and page.get_attribute('#hours-input', 'aria-invalid') == 'true')
        check(f'6.7 часы {h!r} → «{msg}», ввод сохранён', ok, (titles(), err.text_content(), page.input_value('#hours-input')))
    fresh(); add('', '')
    check('6.7 обе ошибки сразу', page.locator('#title-error').is_visible() and page.locator('#hours-error').is_visible())
    check('6.7 фокус на первом невалидном', page.evaluate('document.activeElement.id') == 'title-input')
    page.fill('#title-input', 'x')
    check('6.7 ошибка снимается при вводе', page.locator('#title-error').is_hidden())
    # 6.8
    for h, val in [('0,5', 0.5), ('24', 24), ('1.5', 1.5), ('1,5', 1.5)]:
        fresh(); add('Задача', h)
        check(f'6.8 часы {h!r} приняты', page.evaluate('state.tasks.at(-1).hours') == val and len(titles()) == 4)
    # 6.9
    fresh(); add('Тест', '1,5')
    check('6.9 Тест 1,5: 9,5 ч / 2 ч / 21%', summary() == ('9,5 ч','2 ч','21%'), summary())
    check('6.9 поля очищены', page.input_value('#title-input') == '' and page.input_value('#hours-input') == '')
    fresh(); add('  Конспект  ', '1')
    check('trim: «Конспект»', titles()[-1] == 'Конспект', titles())
    ids = page.evaluate('state.tasks.map(t => t.id)')
    add('Ещё', '1')
    ids2 = page.evaluate('state.tasks.map(t => t.id)')
    check('id уникальны', len(set(ids2)) == len(ids2), ids2)
    # 6.10
    fresh(); delete('Чтение')
    check('6.10 − Чтение: 6/0/0%', summary() == ('6 ч','0 ч','0%'), summary())
    check('6.10 удалено из данных', page.evaluate('state.tasks.length') == 2)
    delete('Практика'); delete('Повторение')
    body = page.inner_text('body')
    check('6.10 все удалены: 0/0/0%', summary() == ('0 ч','0 ч','0%'), summary())
    check('6.10 нет NaN/Infinity', 'NaN' not in body and 'Infinity' not in body)
    check('6.10 текст «Задач нет»', page.locator('#empty-text').is_visible() and page.text_content('#empty-text') == 'Задач нет')
    fresh(); toggle('Чтение')
    check('снятие отметки Чтение: 0 ч / 0%', summary() == ('8 ч','0 ч','0%'), summary())
    # 6.11
    fresh()
    sw = lambda: page.evaluate('[document.documentElement.scrollWidth, innerWidth]')
    w = sw(); check('6.11 390 px: нет гор. скролла (старт)', w[0] <= w[1], w)
    add('А'*60, '2'); w = sw()
    check('6.11 название 60 символов: нет гор. скролла', w[0] <= w[1], w)
    add('', ''); w = sw()
    check('6.11 с ошибками: нет гор. скролла', w[0] <= w[1], w)
    page.screenshot(path=str(path.parent / 'tests' / 'screenshot-390px.png'), full_page=True)
    # 6.12
    a11y = page.evaluate('''() => {
      const bad = [];
      document.querySelectorAll('input').forEach(i => { if (!i.labels || i.labels.length === 0) bad.push('input ' + (i.id || i.name)); });
      document.querySelectorAll('button').forEach(b => { const n = (b.getAttribute('aria-label') || b.textContent).trim(); if (!n) bad.push('button'); });
      return bad;
    }''')
    check('6.12 у всех input есть label, у кнопок имя', a11y == [], a11y)
    check('6.12 фильтр: legend', page.text_content('.filter legend') == 'Фильтр')
    check('6.12 кнопка удаления называет задачу', page.get_by_role('button', name='Удалить «Практика»').count() == 1)
    # 6.2
    check('6.2 нет запросов кроме самого файла', all(u.startswith('file://') for u in reqs), [u for u in reqs if not u.startswith('file://')])
    check('нет ошибок JS в консоли', errors == [], errors)
    b.close()

fails = [r for r in results if not r[1]]
for n, ok, d in results:
    print(('OK  ' if ok else 'FAIL'), n, '' if ok else d)
print(f'\nИтого: {len(results)-len(fails)}/{len(results)} пройдено')
