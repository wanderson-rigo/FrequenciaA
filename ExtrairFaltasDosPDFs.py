import csv
import glob
import os
import re
import pdfplumber
import requests
from datetime import datetime

PASTA_PDFS = "./pdfs"  # Defina a pasta onde estão os arquivos PDFs
CSV_FINAL_PATH = "./saida/faltas.csv"

SUPABASE_URL = os.environ.get('SUPABASE_URL')
SUPABASE_KEY = os.environ.get('SUPABASE_KEY')


def extrair_datas_reais_cabecalho(tabela):
    """
    Mapeia e reconstrói dinamicamente as datas (DD/MM/AAAA) de cada coluna,
    associando os meses às suas respectivas colunas de dias e aplicando a lógica
    de que os dias aumentam até no máximo 31 dentro de cada mês.
    """
    mapa_meses_nomes = {
        "jan": 1, "fev": 2, "mar": 3, "abr": 4, "mai": 5, "jun": 6,
        "jul": 7, "ago": 8, "set": 9, "out": 10, "nov": 11, "dez": 12
    }
    
    linha_meses = None
    linha_dias = None
    
    # Procura as linhas de cabeçalho (Meses e Dias) nas primeiras linhas da tabela
    for idx, linha in enumerate(tabela[:5]):
        linha_str = " ".join([str(c) for c in linha if c]).lower()
        if any(m in linha_str for m in mapa_meses_nomes.keys()) and not linha_meses:
            linha_meses = linha
        if "matrícula" in linha_str or "matricula" in [str(c).lower() for c in linha if c]:
            linha_dias = linha
            if not linha_meses and idx > 0:
                linha_meses = tabela[idx - 1]
            break

    if not linha_dias: 
        return []

    datas_por_coluna = []
    mes_atual = 2  # Início padrão (Fevereiro)
    ano_atual = 2026  # Ano base padrão do diário
    ultimo_dia_visto = 0
    hoje = datetime.now().date()

    # As colunas de aulas começam no índice 2 (após Matrícula e Nome)
    for idx in range(2, len(linha_dias)):
        celula_mes = str(linha_meses[idx]).lower() if idx < len(linha_meses) and linha_meses[idx] else ""
        celula_dia = str(linha_dias[idx]) if linha_dias[idx] else ""

        # Atualiza o mês corrente ao encontrá-lo explicitamente no cabeçalho
        for nome, num in mapa_meses_nomes.items():
            if nome in celula_mes:
                if num < mes_atual and num == 1: 
                    ano_atual += 1
                mes_atual = num
                ultimo_dia_visto = 0  # Reseta o rastreamento para o novo mês explícito
                break

        # Limpa quebras de linha ou caracteres residuais do dia (ex: "10\n g" -> "10")
        dias = re.findall(r"\b\d{1,2}\b", celula_dia)
        datas_desta_coluna = []

        for d_str in dias:
            dia = int(d_str)
            
            # Lógica sugerida: se o dia diminuiu sem mudar o mês explicitamente, o mês virou
            if dia < ultimo_dia_visto:
                mes_atual += 1
                if mes_atual > 12:
                    mes_atual = 1
                    ano_atual += 1
            
            try:
                data_obj = datetime(ano_atual, mes_atual, dia).date()
                # As datas sempre serão mais antigas ou iguais ao dia de hoje
                if data_obj <= hoje:
                    datas_desta_coluna.append(data_obj.strftime("%d/%m/%Y"))
                ultimo_dia_visto = dia
            except ValueError:
                continue

        # Se chegarmos nas colunas de encerramento/totais ou vazias, marcamos para alinhamento
        if not datas_desta_coluna:
            if any(x in celula_dia for x in ["Total", "Qtd", "%CH", "%AL"]):
                break
            datas_por_coluna.append(["VAZIO_OU_FERIADO"])
        else:
            datas_por_coluna.append(datas_desta_coluna)

    return datas_por_coluna


def extrair_dados_de_um_pdf(pdf_path):
    linhas_deste_pdf = []

    with pdfplumber.open(pdf_path) as pdf:
        # --- 1. METADADOS DO CABEÇALHO ---
        primeira_pagina = pdf.pages[0]
        texto_cabecalho = primeira_pagina.extract_text()

        codigo_disciplina = "Desconhecido"
        disciplina = "Desconhecida"
        turma = "01"
        carga_horaria = 0
        aulas_ministradas = 0

        for linha in texto_cabecalho.split("\n"):
            if "Turma:" in linha:
                match_turma = re.search(r"Turma:\s*([0-9A-Za-z]+)", linha)
                if match_turma:
                    turma = match_turma.group(1)

            if "Disciplina:" in linha:
                conteudo_disciplina = linha.replace("Disciplina:", "").strip()
                if "-" in conteudo_disciplina:
                    partes = conteudo_disciplina.split("-", 1)
                    codigo_disciplina = partes[0].strip()
                    disciplina = partes[1].strip()
                else:
                    codigo_disciplina = conteudo_disciplina

            elif "Total de aulas" in linha or "definido pela CH:" in linha:
                match_ch = re.search(r"CH:\s*(\d+)", linha)
                if match_ch:
                    carga_horaria = int(match_ch.group(1))

            elif "Número de aulas ministradas" in linha:
                match_min = re.search(r"frequência\):\s*(\d+)", linha)
                if match_min:
                    aulas_ministradas = int(match_min.group(1))

        percentual_ministrado = (
            round((aulas_ministradas / carga_horaria) * 100, 2)
            if carga_horaria > 0
            else 0.0
        )

        # --- 2. PROCESSAMENTO DAS TABELAS ---
        datas_mapeadas = []

        for num_pag, pagina in enumerate(pdf.pages):
            tabelas = pagina.extract_tables()
            if not tabelas:
                continue

            for tabela in tabelas:
                # Obtém o mapa de datas reais usando a tabela da primeira página
                if num_pag == 0 and not datas_mapeadas:
                    datas_mapeadas = extrair_datas_reais_cabecalho(tabela)

                for linha in tabela:
                    if not linha or not linha[0] or "Matrícula" in str(linha[0]):
                        continue

                    # Limpeza e tratamento de linhas aglutinadas (\n)
                    celulas_limpas = [str(cel).strip() if cel is not None else "" for cel in linha]

                    matriculas = celulas_limpas[0].split("\n")
                    nomes = celulas_limpas[1].split("\n")
                    
                    # Localiza a coluna do Total de Faltas para delimitar o fim do histórico
                    total_idx = -1
                    for idx, cel in enumerate(reversed(celulas_limpas)):
                        if cel.replace("\n", "").strip().isdigit() and idx > 0:
                            total_idx = len(celulas_limpas) - 1 - idx
                            break
                    
                    if total_idx == -1:
                        continue
                        
                    totais_pdf = celulas_limpas[total_idx].split("\n")

                    if not matriculas[0].isdigit():
                        continue

                    # Grade central contendo estritamente os lançamentos de frequência
                    historico_colunas_bruto = celulas_limpas[2:total_idx]

                    # Varre a lista de alunos (incluindo tratamento para linhas aglutinadas)
                    for idx_sub in range(len(matriculas)):
                        mat_aluno = matriculas[idx_sub].strip()
                        if not mat_aluno.isdigit():
                            continue
                        nome_aluno = nomes[idx_sub].strip() if idx_sub < len(nomes) else nomes[0].strip()

                        try:
                            total_faltas_pdf = int(totais_pdf[idx_sub].strip())
                        except (IndexError, ValueError):
                            total_faltas_pdf = int(totais_pdf[0].strip()) if totais_pdf else 0

                        # Cálculo do percentual de faltas e situação de reprovação (> 25%)
                        percentual_faltas = (
                            round((total_faltas_pdf / carga_horaria) * 100, 2)
                            if carga_horaria > 0
                            else 0.0
                        )
                        situacao = "REPROVADO POR FALTAS" if percentual_faltas > 25.0 else "FREQUÊNCIA OK"

                        # Cruza cada coluna de faltas com sua respectiva data
                        for idx_aula, datas_alvo in enumerate(datas_mapeadas):
                            if idx_aula >= len(historico_colunas_bruto):
                                break
                            
                            # Se a coluna do cabeçalho correspondia a um feriado/vazio, ignora
                            if "VAZIO" in datas_alvo[0]:
                                continue

                            conteudo_celula = historico_colunas_bruto[idx_aula]
                            sub_faltas = conteudo_celula.split("\n")
                            num_datas = len(datas_alvo)
                            
                            # Mapeamento do bloco exato de dados para o aluno correspondente
                            fatiamento = sub_faltas[idx_sub * num_datas : (idx_sub + 1) * num_datas]

                            for i_data, data_final in enumerate(datas_alvo):
                                if i_data < len(fatiamento):
                                    falta_texto = fatiamento[i_data].strip()
                                    
                                    # Filtra rigorosamente: apenas valores numéricos maiores que ZERO são adicionados
                                    if falta_texto.isdigit():
                                        qtd_faltas = int(falta_texto)
                                        
                                        if qtd_faltas > 0:
                                            linhas_deste_pdf.append({
                                                "codigo_disciplina": codigo_disciplina,
                                                "disciplina":  disciplina,
                                                "turma": turma,
                                                "matricula": mat_aluno,
                                                "nome": nome_aluno,
                                                "aula": idx_aula + 1,
                                                "data": data_final,
                                                "faltas": qtd_faltas,
                                                "total_faltas_pdf": total_faltas_pdf,
                                                "carga_horaria": carga_horaria,
                                                "aulas_ministradas": aulas_ministradas,
                                                "percentual_ministrado": f"{percentual_ministrado}%",
                                                "percentual_faltas": f"{percentual_faltas}%",
                                                "situacao": situacao,
                                            })

    return linhas_deste_pdf


def salvar_faltas_supabase(dados, colunas):
    """Envia os dados extraídos para a tabela 'faltas' do Supabase."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        print("ERRO: SUPABASE_URL ou SUPABASE_KEY não definidos no ambiente.")
        return False

    table = 'faltas'
    base_url = SUPABASE_URL.rstrip('/') + f'/rest/v1/{table}'
    headers = {
        'apikey': SUPABASE_KEY,
        'Authorization': f'Bearer {SUPABASE_KEY}',
        'Content-Type': 'application/json'
    }

    # Inserir em lotes (merge-duplicates faz upsert automático)
    batch_size = 200
    inserted = 0
    try:
        for i in range(0, len(dados), batch_size):
            batch = dados[i:i+batch_size]
            print(f"Inserindo lote {i//batch_size + 1} ({len(batch)} registros)...")
            r_insert = requests.post(
                base_url,
                headers={**headers, 'Prefer': 'resolution=merge-duplicates'},
                json=batch,
                timeout=30
            )
            if r_insert.status_code not in (200, 201):
                print(f"ERRO ao inserir lote: {r_insert.status_code} - {r_insert.text}")
                return False
            inserted += len(batch)
        print(f"✓ {inserted} registros inseridos com sucesso no Supabase!")
        return True
    except Exception as e:
        print(f"ERRO ao inserir dados: {e}")
        return False


# --- PROCESSO DE EXECUÇÃO ---
all_data = []
arquivos_pdf = glob.glob(os.path.join(PASTA_PDFS, "*.pdf"))

if not arquivos_pdf:
    print(f"Nenhum arquivo PDF encontrado na pasta '{PASTA_PDFS}'.")
else:
    print(f"Iniciando processamento de {len(arquivos_pdf)} arquivo(s)...")
    for pdf_file in arquivos_pdf:
        print(f"Filtrando faltas do arquivo: {os.path.basename(pdf_file)}...")
        try:
            dados_pdf = extrair_dados_de_um_pdf(pdf_file)
            all_data.extend(dados_pdf)
        except Exception as e:
            print(f"Erro ao processar o arquivo {os.path.basename(pdf_file)}: {e}")

    # Gravação dos dados filtrados no CSV com as novas colunas
    colunas = [
        "codigo_disciplina",
        "disciplina",
        "turma",
        "matricula",
        "nome",
        "aula",
        "data",
        "faltas",
        "total_faltas_pdf",
        "carga_horaria",
        "aulas_ministradas",
        "percentual_ministrado",
        "percentual_faltas",
        "situacao",
    ]

    os.makedirs(os.path.dirname(CSV_FINAL_PATH), exist_ok=True)

    with open(CSV_FINAL_PATH, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=colunas)
        writer.writeheader()
        writer.writerows(all_data)

    salvar_faltas_supabase(all_data, colunas)

    print("\n" + "=" * 60)
    print(f"Filtro concluído! Arquivo gerado: '{CSV_FINAL_PATH}'")
    print(f"Dados enviados para Supabase (tabela: faltas)")
    print(f"Total de registros de faltas (> 0) salvos: {len(all_data)} linhas.")
    print("=" * 60)
