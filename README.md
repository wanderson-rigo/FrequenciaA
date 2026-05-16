# Sistema de Frequência

Este sistema foi desenvolvido pelo prof. Wanderson Rigo do IFC-Videira para capturar os diários de frequência  dos alunos no SIGAA, gerar um arquivo CSV e então extrair estatísticas dos dados.

Basta editar os nomes dos alunos de interesse no arquivo alunos.txt

O arquivo CSV gerado pode ser manipulado de forma independente para geração de estatíticas, por exemplo.

Para explorar os dados CSV gerados, pode ser usado o programa FrequenciaA.exe, que precisa carregar o arquivo CSV e então abre um navegador em http://127.0.0.1:8050 onde podem ser realizados filtros e consultas.

## Detalhes técnicos

Programado em Python valendo-se principalmente das APIs selenium e ...

As configurações a serem definidas no arquivo *config.json* são:

- "URL": "https://sig.ifc.edu.br/sigaa/verTelaLogin.do", do SIGAA
- "USERNAME": "fulano.sobrenome", nome de usuário do SIGAA
- "PASSWORD": "senha", a senha do SIGAA. Se não preencher aqui, uma caixa de diálogo vai pedir a senha.
- "STUDANTS_NAMES": "alunos.txt", nome do arquivo que contém os nomes dos estudantes.
- "STUDANTS_FREQ": "freq_alunos.csv"