import csv
import json
from logging import config
import os
import time
from tkinter import simpledialog
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
import tkinter as tk
from selenium import webdriver
from selenium.webdriver.common.alert import Alert

config = None

def extrair_notas_sigaa():
    URL = config.get("URL")
    USERNAME = config.get("USERNAME")

    #se fazio, perguntar com diálogo
    if not USERNAME:
        user = simpledialog.askstring("Usuário", "Digite o seu usuário de acesso ao SIGAA:", initialvalue="")
        USERNAME = user

    PASSWORD = config.get("PASSWORD")

    #se fazio, perguntar com diálogo
    if not PASSWORD:
        password = simpledialog.askstring("Senha", "Digite a sua senha de acesso ao SIGAA:", initialvalue="", show="*")
        PASSWORD = password

    STUDANTS_NAMES = config.get("STUDANTS_NAMES")

    ALUNOS = []
    # Carregar lista de alunos do diretório nomes/alunos.txt
    with open(STUDANTS_NAMES, "r", encoding="utf-8") as arquivo:
        for linha in arquivo:
            ALUNOS.append(linha.strip())

    # Inicialize o driver do navegador
    browser = webdriver.Firefox()
    browser.maximize_window()  # Maximize a janela do navegador
    browser.get(URL)

    # Faça login
    username_field = browser.find_element(By.NAME, "user.login")
    username_field.send_keys(USERNAME)
    password_field = browser.find_element(By.NAME, "user.senha")
    password_field.send_keys(PASSWORD)
    password_field.send_keys(Keys.RETURN)

    # Aguarde até que a página da tabela seja carregada
    WebDriverWait(browser, 10).until(
        EC.presence_of_element_located((By.XPATH, "//table[@class='listagem table tabela-selecao-vinculo']")))

    # Navegue até a página desejada
    browser.find_element(By.XPATH, "//a[@class='withoutFormat' and contains(text(),'Secretário')]").click()
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//li[@class='graduacao on']")))
    browser.find_element(By.XPATH, "//a[@href='/sigaa/verMenuGraduacao.do']").click()

     # Ciente
    browser.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()

    browser.find_element(By.XPATH, "//span[text() = 'Alunos']").click()

    wait = WebDriverWait(browser, 10)

    # 1. esperar o link existir (não precisa estar visível)
    link = wait.until(EC.presence_of_element_located(
        (By.XPATH, "//a[contains(normalize-space(), 'Consultar Dados do Aluno')]")
    ))

    # 2. pegar o onclick real
    onclick = link.get_attribute("onclick")

    # 3. executar exatamente o que o sistema executa
    browser.execute_script(onclick)

     # Pegar dados de todos os alunos
    dados_alunos = []
    for aluno in ALUNOS:
        dados_aluno = pegar_dados_aluno(aluno)
               
        print(f'Dados do aluno {aluno} capturados com sucesso!')


        dados_alunos.append(dados_aluno)


def pegar_dados_aluno(aluno):
    browser.find_element(By.ID, "formulario:nomeDiscente").clear()
    browser.find_element(By.ID, "formulario:nomeDiscente").send_keys(aluno)
    browser.find_element(By.ID, "formulario:buscar").click()

    # Selecionar todas as linhas da tabela com as classes 'linhaPar' ou 'linhaImpar',
    # excluindo 'curso' e linhas que contêm um <td> com a classe 'detalhesDiscente'
    linhas = browser.find_elements(By.XPATH, 
    "//table[@class='listagem']/tbody/tr[not(contains(@class, 'curso')) and " \
    "(contains(@class, 'linhaPar') or contains(@class, 'linhaImpar')) and " \
    "not(td[contains(@class, 'detalhesDiscente')])]")

    # Iterar sobre cada linha da tabela
    for linha in linhas:
        # Obter todas as células (td) da linha
        celulas = linha.find_elements(By.XPATH, ".//td")

        #se o tamanho for maior que 1, tem dados
        if len(celulas) > 1:
            nome = celulas[3].text # nome do aluno
            print(nome)

            status = celulas[5].text # situação do aluno
            print(status)

            ação = celulas[6] # ação de clicar no aluno

            #se o nome do aluno for igual ao nome do aluno que está sendo procurado, e ele for ATIVO clicar nele
            if (nome == aluno) and (status in  "ATIVO"):
                botoes_selecionar = ação.find_element(By.XPATH, ".//input[@title='Selecionar Discente']")
                botoes_selecionar.click()
                break
            else:
                print("Aluno não encontrado ou não está ativo!")

    print("Fechando...")
return dados_alunos


def carregar_configuracoes():
    try:
        with open("config_CCO.json", "r") as config_file:
            config = json.load(config_file)
            print("Configurações carregadas com sucesso!")
            return config
    except Exception as e:
        print("Erro ao carregar as configurações:", e)
        return None

def main():
    try:        
        extrair_notas_sigaa()
        print("Notas extraídas do SIGAA com sucesso!")

    except Exception as e:
        print("Erro ao carregar as configurações:", e)
        print(f"Full exception: {repr(e)}")

if __name__ == "__main__":
    # fallback (mantém funcionando standalone)
    config = carregar_configuracoes()
    main()