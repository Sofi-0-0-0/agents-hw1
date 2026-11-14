"""Автопроверка T1–T5 для tracker-v1.html, tracker-v1-corrected.html и tracker-v2.html.

Установка:  pip install playwright && playwright install chromium
Запуск из папки ИИ_дз1:  python3 tests/run_t1_t5.py .
Свой Chrome:  CHROME_PATH=/путь/к/chrome python3 tests/run_t1_t5.py .
"""
import os, sys, pathlib
from playwright.sync_api import sync_playwright

V1 = dict(total='#totalHours', done='#doneHours', pct='#percent', title='#titleInput', hours='#hoursInput',
          err=lambda p: p.text_content('#error').strip(), active=lambda p: p.click('[data-filter=active]'),
          titles='li.task .task-title', cb=lambda n: f'Отметить «{n}» как готовое', fmt=lambda h: f'{h} ч', comma=False)
V2 = dict(total='#total-hours', done='#done-hours', pct='#progress', title='#title-input', hours='#hours-input',
          err=lambda p: ' | '.join(e.text_content() for e in p.query_selector_all('.error') if e.is_visible()),
          active=lambda p: p.get_by_role('radio', name='Активные').check(),
          titles='.task-title', cb=lambda n: n, fmt=lambda h: f'{h} ч', comma=True)

def run(file, A):
    res = []
    def check(tid, name, cond, detail=''):
        res.append((tid, name, bool(cond), detail))
    with sync_playwright() as pw:
        chrome = os.environ.get('CHROME_PATH')
        b = pw.chromium.launch(executable_path=chrome) if chrome else pw.chromium.launch()
        ctx = b.new_context(viewport={'width': 390, 'height': 844}, locale='ru-RU', offline=True)
        p = ctx.new_page(); errs = []
        p.on('pageerror', lambda e: errs.append(str(e)))
        url = pathlib.Path(file).resolve().as_uri()
        def fresh():
            p.goto(url); p.evaluate('try{localStorage.clear()}catch(e){}'); p.reload()
        S = lambda: (p.text_content(A['total']).strip(), p.text_content(A['done']).strip(), p.text_content(A['pct']).strip())
        T = lambda: p.eval_on_selector_all(A['titles'], 'els => els.map(e => e.textContent)')
        def add(t, h):
            p.fill(A['title'], t); p.fill(A['hours'], h); p.click('button[type=submit]')
        start = ('8 ч', '2 ч', '25%')
        # T1
        fresh()
        check('T1', '3 задачи, 8 ч / 2 ч / 25%', T() == ['Чтение','Практика','Повторение'] and S() == start, (T(), S()))
        # T2
        p.get_by_role('checkbox', name=A['cb']('Практика'), exact=True).click()
        check('T2', 'Практика готова → 6 из 8 ч, 75%', S() == ('8 ч','6 ч','75%'), S())
        if A is V1:
            p.reload()
            check('T2', 'после перезагрузки «Практика» остаётся готовой (localStorage)', S() == ('8 ч','6 ч','75%'), S())
        else:
            check('T2', 'в данных Практика.done = true', p.evaluate("state.tasks.find(t => t.title === 'Практика').done") is True)
        # T3
        fresh(); A['active'](p)
        check('T3', 'Активные: Практика, Повторение; 25%', T() == ['Практика','Повторение'] and S() == start, (T(), S()))
        # T4
        cases = [('', '2', 'пустое название'), ('   ', '2', 'название из пробелов'),
                 ('Задача', '', 'пустые часы'), ('Задача', '-1', 'отрицательные часы'), ('Задача', '0', 'ноль'),
                 ('Задача', '0.4', 'ниже границы 0,4'), ('Задача', '24.5', 'выше границы 24,5'), ('Задача', '25', '25'),
                 ('Задача', '1.2', 'шаг: 1,2'), ('Задача', '0.75', 'шаг: 0,75')]
        if A['comma']: cases += [('Задача', '1,2', 'шаг: 1,2 через запятую'), ('Задача', 'abc', 'не число')]
        for t, h, name in cases:
            fresh(); add(t, h)
            ok = len(T()) == 3 and S() == start and A['err'](p) != '' and p.input_value(A['title']) == t and p.input_value(A['hours']) == h
            check('T4', f'отклонено: {name}', ok, (len(T()), S(), A['err'](p), p.input_value(A['title']), p.input_value(A['hours'])))
        for h, expect_total in [('0.5', '8,5 ч'), ('24', '32 ч'), ('1.5', '9,5 ч')]:
            fresh(); add('Задача', h)
            check('T4', f'принято: {h}', len(T()) == 4 and S()[0] == expect_total, (T(), S(), A['err'](p)))
        # T5
        fresh()
        for n in ['Чтение', 'Практика', 'Повторение']:
            p.get_by_role('button', name=f'Удалить «{n}»').click()
        body = p.inner_text('body')
        check('T5', 'все удалены → 0 ч / 0 ч / 0%', S() == ('0 ч','0 ч','0%'), S())
        check('T5', 'нет NaN/Infinity', 'NaN' not in body and 'Infinity' not in body)
        add('Новая', '2')
        check('T5', 'после удаления всего добавление работает', T() == ['Новая'] and S() == ('2 ч','0 ч','0%'), (T(), S()))
        w = p.evaluate('[document.documentElement.scrollWidth, innerWidth]')
        check('—', '390 px без гор. скролла', w[0] <= w[1], w)
        check('—', 'нет ошибок JS', errs == [], errs)
        b.close()
    return res

folder = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else '.')
for f, A in [('tracker-v1.html', V1), ('tracker-v1-corrected.html', V1), ('tracker-v2.html', V2)]:
    r = run(folder / f, A)
    print(f'\n=== {f}: {sum(x[2] for x in r)}/{len(r)}')
    for tid, n, ok, d in r:
        print(f"  {'OK  ' if ok else 'FAIL'} {tid} {n}" + ('' if ok else f'   → {d}'))
