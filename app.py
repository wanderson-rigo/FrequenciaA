from flask import Flask, jsonify, send_from_directory, request, abort
import os
import csv
import sqlite3

BASE_DIR = os.path.dirname(__file__)
SAIDA_DIR = os.path.join(BASE_DIR, 'saida')

app = Flask(__name__, static_folder='.', static_url_path='')


def safe_path_in_saida(filename):
    # prevent path traversal
    if os.path.isabs(filename) or '..' in filename.replace('\\', '/').split('/'):
        return None
    return os.path.join(SAIDA_DIR, filename)


@app.route('/api/csv')
def api_csv():
    filename = request.args.get('file', 'faltas.csv')
    path = safe_path_in_saida(filename)
    if not path or not os.path.exists(path):
        return jsonify({'error': 'Arquivo CSV não encontrado', 'file': filename}), 404

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [row for row in reader]

    return jsonify(rows)


@app.route('/api/sqlite')
def api_sqlite():
    filename = request.args.get('file')

    # choose a sqlite file inside saida
    candidates = []
    if filename:
        p = safe_path_in_saida(filename)
        if p and os.path.exists(p):
            candidates = [p]
    else:
        if os.path.isdir(SAIDA_DIR):
            for name in os.listdir(SAIDA_DIR):
                if name.lower().endswith(('.sqlite', '.db', '.db3')):
                    candidates.append(os.path.join(SAIDA_DIR, name))

    if not candidates:
        return jsonify({'error': 'Nenhum arquivo sqlite encontrado em saida'}), 404

    db_path = candidates[0]

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # list tables
    cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name")
    tables = [r[0] for r in cur.fetchall()]
    if not tables:
        conn.close()
        return jsonify({'table': None, 'columns': [], 'rows': []})

    table = tables[0]

    # get columns
    cur.execute(f"PRAGMA table_info({table})")
    cols = [r[1] for r in cur.fetchall()]

    cur.execute(f"SELECT * FROM {table} LIMIT 5000")
    rows = [list(r) for r in cur.fetchall()]
    conn.close()

    return jsonify({'table': table, 'columns': cols, 'rows': rows})


@app.route('/')
def index():
    return send_from_directory('.', 'index.html')


@app.route('/<path:path>')
def static_proxy(path):
    # serve other static files
    return send_from_directory('.', path)


if __name__ == '__main__':
    # run on localhost:5000
    app.run(host='0.0.0.0', port=5000, debug=True)
