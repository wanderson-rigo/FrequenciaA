"""
Upload `saida/faltas.csv` to Supabase table `faltas` via REST.

Set environment variables:
  SUPABASE_URL (ex: https://xyz.supabase.co)
  SUPABASE_KEY (service_role or anon key with insert permissions)

Usage:
  python upload_to_supabase.py

The script does NOT create the table. Use `supabase_schema.sql` to create the table in Supabase SQL editor.
"""
import os
import csv
import requests

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')
BASE_DIR = os.path.dirname(__file__)
SAIDA_DIR = os.path.join(BASE_DIR, 'saida')


def main():
    if not SUPABASE_URL or not SUPABASE_KEY:
        print('Defina SUPABASE_URL e SUPABASE_KEY no ambiente antes de executar.')
        return

    path = os.path.join(SAIDA_DIR, 'faltas.csv')
    if not os.path.exists(path):
        print('Arquivo saida/faltas.csv não encontrado.')
        return

    with open(path, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = [r for r in reader]

    url = f"{SUPABASE_URL.rstrip('/')}/rest/v1/faltas"
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates'
    }

    # send in batches
    batch_size = 200
    for i in range(0, len(rows), batch_size):
        batch = rows[i:i+batch_size]
        try:
            r = requests.post(url, headers=headers, json=batch, timeout=30)
            if r.status_code not in (200, 201):
                print('Erro ao enviar lote', i, r.status_code, r.text)
                return
            print(f'Lote {i//batch_size + 1} enviado ({len(batch)} registros)')
        except Exception as e:
            print('Exceção ao enviar lote', i, e)
            return

    print('Upload concluído.')


if __name__ == '__main__':
    main()
