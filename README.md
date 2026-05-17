# Sistema de Frequência

Este sistema foi desenvolvido pelo prof. Wanderson Rigo do IFC-Videira para capturar os diários de frequência  dos alunos no SIGAA, gerar um arquivo CSV e SQLite então extrair estatísticas dos dados.

Basta editar os nomes dos alunos de interesse no arquivo nomes/alunos.txt

O arquivo CSV gerado pode ser manipulado de forma independente para geração de estatíticas, por exemplo.

Para explorar os dados gerados clique [aqui](https://frequenciaa.onrender.com)

## Deploy no Render

Este projeto pode ser publicado no Render como um serviço Python.

1. Adicione o repositório no Render.
2. Use o build command:
   - `pip install -r requirements.txt`
3. Use o start command:
   - `gunicorn app:app --bind 0.0.0.0:$PORT`
4. Defina as variáveis de ambiente no painel do serviço:
   - `SUPABASE_URL`
   - `SUPABASE_KEY`

O `Procfile` e o `requirements.txt` já foram ajustados para suporte.

## Detalhes técnicos

Programado em Python e API Selenium