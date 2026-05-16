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
