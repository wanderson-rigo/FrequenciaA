Instruções rápidas para executar o servidor local

1. Crie um ambiente virtual (recomendado) e instale dependências:

```bash
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
```

2. Inicie o servidor Flask:

```bash
python app.py
```

3. Abra no navegador:

http://localhost:5000/index.html

O servidor expõe as APIs:
- `/api/csv?file=faltas.csv` — retorna o CSV em `saida/faltas.csv` como JSON
- `/api/sqlite` — procura um arquivo SQLite em `saida/` e retorna a primeira tabela como JSON

Suporte a Supabase:
- Defina as variáveis de ambiente `SUPABASE_URL` e `SUPABASE_KEY` (service_role ou anon conforme permissões).
- Use `supabase_schema.sql` no SQL editor do Supabase para criar a tabela `faltas`.
- Para enviar o CSV para o Supabase, use:

```bash
set SUPABASE_URL=https://xyz.supabase.co
set SUPABASE_KEY=your_key_here
python upload_to_supabase.py
```

- Endpoint proxy: `/api/supabase` buscará a tabela `faltas` no Supabase e retornará no mesmo formato JSON usado por `/api/sqlite`.
