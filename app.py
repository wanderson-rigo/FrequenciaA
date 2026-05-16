from flask import Flask, jsonify, send_from_directory, request, abort
import os
import csv
import sqlite3
import requests
import json

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')

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


@app.route('/api/supabase')
def api_supabase():
    """Proxy to Supabase REST for table 'faltas'. Requires SUPABASE_URL and SUPABASE_KEY in env."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({'error': 'SUPABASE_URL or SUPABASE_KEY not configured in environment'}), 500

    table = request.args.get('table', 'faltas')
    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/{table}"

    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Accept': 'application/json'
    }

    params = {'select': '*'}

    try:
        r = requests.get(url, headers=headers, params=params, timeout=10)
        r.raise_for_status()
    except Exception as e:
        return jsonify({'error': 'Falha ao consultar Supabase', 'detail': str(e)}), 502

    data = r.json()

    if not isinstance(data, list):
        return jsonify({'error': 'Resposta inesperada da Supabase', 'data': data}), 502

    # columns are keys of first row
    if data:
        cols = list(data[0].keys())
        rows = [[row.get(c) for c in cols] for row in data]
    else:
        cols = []
        rows = []

    return jsonify({'table': table, 'columns': cols, 'rows': rows})


@app.route('/api/upload_csv', methods=['POST'])
def api_upload_csv():
    """Receive a CSV file and replace the Supabase `faltas` table contents.
    Requires SUPABASE_URL and SUPABASE_KEY set in environment (service_role key).
    """
    if not SUPABASE_URL or not SUPABASE_KEY:
        return jsonify({'error': 'SUPABASE_URL or SUPABASE_KEY not configured in environment'}), 500

    if 'file' not in request.files:
        return jsonify({'error': 'Arquivo CSV não enviado (campo file)'}), 400

    f = request.files['file']
    try:
        # parse CSV into list of dicts
        import io
        s = io.StringIO(f.stream.read().decode('utf-8'))
        reader = csv.DictReader(s)
        rows = [r for r in reader]
    except Exception as e:
        return jsonify({'error': 'Falha ao ler CSV', 'detail': str(e)}), 400

    table = 'faltas'
    base = SUPABASE_URL.rstrip('/') + f'/rest/v1/{table}'
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    # clear table
    try:
        rdel = requests.delete(base, headers={**headers, 'Prefer': 'return=representation'}, timeout=20)
        # allow 200/204 responses
        if rdel.status_code not in (200, 204):
            return jsonify({'error': 'Falha ao limpar tabela no Supabase', 'status': rdel.status_code, 'detail': rdel.text}), 502
    except Exception as e:
        return jsonify({'error': 'Exceção ao limpar tabela', 'detail': str(e)}), 502

    # insert in batches
    batch_size = 200
    inserted = 0
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        try:
            r = requests.post(base, headers={**headers, 'Prefer': 'resolution=merge-duplicates'}, json=batch, timeout=30)
            if r.status_code not in (200, 201):
                return jsonify({'error': 'Falha ao inserir lote', 'index': i, 'status': r.status_code, 'detail': r.text}), 502
            inserted += len(batch)
        except Exception as e:
            return jsonify({'error': 'Exceção ao inserir lote', 'index': i, 'detail': str(e)}), 502

    return jsonify({'status': 'ok', 'inserted': inserted, 'rows': len(rows)})


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
