from flask import Blueprint, render_template, redirect, flash, url_for
from flask_login import login_required
from app.db import get_connection

main = Blueprint('main', __name__)

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

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/testdb')
def test_connection():
    try:
        with get_connection():
            flash("Подключение к БД успешно", "success")
    except Exception as e:
        flash(f"Ошибка подключения к БД: {e}", "danger")
    return redirect(url_for('main.index'))

@main.route('/radicals', methods=['GET'])
def radicals():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute('''
                    SELECT lo.symbol, lo.pinyin_base, lo.tone, lo.meaning, lo.strokes, rg.name
                    FROM "learning_object" as lo
                    LEFT JOIN "radical_group" rg ON lo.group_id = rg.id
                    ''')
        rows = cur.fetchall()
        updated_rows = [
            (symbol, add_accent(pinyin_base, tone), meaning, strokes, name)
            for (
                symbol, pinyin_base, tone, meaning, strokes, name
            ) in rows
        ]
        return render_template('radicals.html', title='Радикалы',
                               rad_symbols=updated_rows)