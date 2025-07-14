import random
import re
from flask import Blueprint, render_template, redirect, request, url_for, flash
from flask_login import login_required, current_user
from app.db import get_connection
import unicodedata

training = Blueprint('training', __name__)

def normalize(text, strip_tones=False):
    text = unicodedata.normalize('NFKD', text)  # разбивает диакритики
    if strip_tones:
        text = ''.join(c for c in text if not unicodedata.combining(c))  # убирает тоны
    text = text.lower().strip()
    text = re.sub(r'\s+', ' ', text)
    return text

def is_answer_correct(user_answer, correct_value):
    # Нормализуем без тонов для пиньиня
    normalized_user = normalize(user_answer, strip_tones=True)
    allowed = [normalize(part, strip_tones=True) for part in re.split(r'[;,/|]', correct_value)]
    return normalized_user in allowed

def add_accent(pinyin_base, tone):
        tones = {
            'a': ['ā', 'á', 'ǎ', 'à'],
            'o': ['ō', 'ó', 'ǒ', 'ò'],
            'e': ['ē', 'é', 'ě', 'è'],
            'i': ['ī', 'í', 'ǐ', 'ì'],
            'u': ['ū', 'ú', 'ǔ', 'ù'],
            'ü': ['ǖ', 'ǘ', 'ǚ', 'ǜ']
        }
        for vowel in tones:
            if vowel in pinyin_base:
                idx = pinyin_base.find(vowel)
                try:
                    new_char = tones[vowel][tone - 1]
                    return pinyin_base[:idx] + new_char + pinyin_base[idx+1:]
                except IndexError:
                    return pinyin_base
        return pinyin_base

@training.route('/start/', methods=['GET','POST'])
@login_required
def start_training():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute ('''
                     SELECT id, name FROM "training_mode"
                     WHERE access_level >= %s
                     ''',
                     (current_user.role_id,))
        modes = cur.fetchall()
    
    if request.method == 'POST':
        selected_mode = request.form['mode_id']
        return redirect(url_for('training.training_session', mode_id=selected_mode))

    return render_template('training/select_mode.html', modes=modes)

@training.route('/<int:mode_id>', methods=['GET', 'POST'])
@login_required
def training_session(mode_id):
    with get_connection() as conn:
        cur = conn.cursor()
        
        # Создание сессии
        cur.execute('''
                    INSERT INTO training_session (user_id, mode_id, date_started)
                    VALUES (%s, %s, CURRENT_DATE)
                    RETURNING id
                    ''', (current_user.id, mode_id))
        session_id = cur.fetchone()[0]

        # Выбор 10 случайных иероглифов 
        cur.execute('''
                    SELECT id FROM learning_object
                    ORDER BY random() LIMIT 4
                    ''')
        object_ids = [row[0] for row in cur.fetchall()]

        # Добавление предметов в training_item
        for object_id in object_ids:
            cur.execute('''
                        INSERT INTO training_item (session_id, object_id)
                        VALUES (%s, %s)
                        ''', (session_id, object_id))
        conn.commit()

    return redirect(url_for('training.training_question', session_id=session_id, index=0))

@training.route('/<int:session_id>/question/<int:index>', methods=['GET', 'POST'])
@login_required
def training_question(session_id, index):
    with get_connection() as conn:
        cur = conn.cursor()

        # Получить training_items по порядку
        cur.execute('''
                    SELECT ti.id, lo.symbol, lo.meaning, lo.pinyin_base, lo.tone
                    FROM training_item ti
                    JOIN learning_object lo ON ti.object_id = lo.id
                    WHERE ti.session_id = %s
                    ORDER BY ti.id
                    ''', (session_id,))
        items = cur.fetchall()

        # Получаем режим тренировки
        cur.execute('SELECT mode_id FROM training_session WHERE id = %s', (session_id,))
        mode_id = cur.fetchone()[0]

    if index >= len(items):
        return redirect(url_for('training.training_result', session_id=session_id))

    item_id, symbol, meaning, pinyin_base, tone = items[index]
    pinyin = add_accent(pinyin_base, tone)

    # Выбор режима тренировки
    if mode_id in [1, 2, 5, 6]:
        # Выбор из 4 вариантов
        if mode_id == 1:
            prompt = symbol
            correct = meaning
            label = "Выберите значение:"
            field = 'meaning'
        elif mode_id == 2:
            prompt = pinyin
            correct = meaning
            label = "Выберите значение:"
            field = 'meaning'
        elif mode_id == 5:
            prompt = meaning
            correct = pinyin
            label = "Выберите пиньинь:"
            field = 'pinyin_base'
        elif mode_id == 6:
            prompt = symbol
            correct = pinyin
            label = "Выберите пиньинь:"
            field = 'pinyin_base'

        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute(f'''
                        SELECT {field}, tone FROM (
                            SELECT DISTINCT {field}, tone FROM learning_object
                            WHERE {field} IS NOT NULL AND NOT ({field} = %s AND tone = %s)
                        ) AS sub
                        ORDER BY RANDOM()
                        LIMIT 3
                        ''', (pinyin_base if 'pinyin_base' in field else correct, tone if 'pinyin_base' in field else None))
            rows = cur.fetchall()
            if 'pinyin_base' in field:
                wrong_options = [add_accent(row[0], row[1]) for row in rows]
            else:
                wrong_options = [row[0] for row in rows]

        options = wrong_options + [correct]
        random.shuffle(options)

        if request.method == 'POST':
            answer = request.form['answer']
            is_correct = answer == correct

            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute('''
                            UPDATE training_item
                            SET is_correct = %s, user_answer = %s
                            WHERE id = %s
                            ''', (is_correct, answer.strip(), item_id))
                conn.commit()

            flash(f"{'✅ Правильно!' if is_correct else f'❌ Неверно. Правильно: ' + correct}")

            return redirect(url_for('training.training_question', session_id=session_id, index=index + 1))

        return render_template(
            'training/question_choice.html',
            prompt=prompt,
            options=options,
            label=label,
            index=index + 1,
            total=len(items),
            mode_id=mode_id
        )

    elif mode_id in [3, 4]:
        # Режимы с HanziWriter + альтернатива ручному вводу
        prompt = meaning if mode_id == 3 else pinyin
        correct = symbol
        label = "Напишите иероглиф:"

        if request.method == 'POST':
            answer = request.form['answer']
            is_correct = normalize(answer) == normalize(correct)

            with get_connection() as conn:
                cur = conn.cursor()
                cur.execute('''
                            UPDATE training_item
                            SET is_correct = %s, user_answer = %s
                            WHERE id = %s
                            ''', (is_correct, answer.strip(), item_id))
                conn.commit()

            return redirect(url_for('training.training_question', session_id=session_id, index=index + 1))

        return render_template(
            'training/question_stroke.html',
            prompt=prompt,
            correct=correct,
            label=label,
            index=index + 1,
            total=len(items),
            mode_id=mode_id
        )

    else:
        return "Неизвестный режим", 400

@training.route('/<int:session_id>/result')
@login_required
def training_result(session_id):
    with get_connection() as conn:
        cur = conn.cursor()

        # Получить все ответы пользователя по тренировке
        cur.execute('''
                    SELECT ts.mode_id, lo.symbol, lo.meaning, lo.pinyin_base, lo.tone,
                        ti.user_answer, ti.is_correct
                    FROM training_item ti
                    JOIN learning_object lo ON ti.object_id = lo.id
                    JOIN training_session ts ON ti.session_id = ts.id
                    WHERE ti.session_id = %s
                    ORDER BY ti.id
                    ''', (session_id,))
        rows = cur.fetchall()
        updated_rows = [
            (mode_id, symbol, meaning, add_accent(pinyin, tone), user_answer, is_correct)
            for (
                mode_id, symbol, meaning, pinyin, tone, user_answer, is_correct
            ) in rows
        ]

        # Определим количество правильных ответов
        correct_count = sum(1 for row in rows if row[5])
        total = len(rows)
        correct_percent = round((correct_count / total) * 100, 2)
        result_string = f"{correct_count} из {total} ({correct_percent} %)"

        # Обновим таблицу training_session с результатом и датой окончания
        cur.execute('''
                    UPDATE training_session
                    SET date_ended = CURRENT_TIMESTAMP, result = %s
                    WHERE id = %s
                    ''', (result_string, session_id))
        conn.commit()

    return render_template('training/result.html', results=updated_rows, result_string=result_string)

@training.route('/history')
@login_required
def history():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
                    SELECT ts.id, ts.date_started, ts.date_ended, tm.name, ts.result
                    FROM training_session ts
                    JOIN training_mode tm ON ts.mode_id = tm.id
                    WHERE ts.user_id = %s
                    ORDER BY ts.date_started DESC
                    ''', (current_user.id,))
        sessions = cur.fetchall()

    return render_template('training/history.html', sessions=sessions)
