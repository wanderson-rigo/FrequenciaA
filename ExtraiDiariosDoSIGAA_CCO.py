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
from selenium.common.exceptions import NoSuchElementException
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
    browser.find_element(By.XPATH, "//a[@class='withoutFormat' and contains(text(),'Vice-Chefia/Vice-Diretoria')]").click()
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//li[@class='portal_graduacao on']")))
    browser.find_element(By.XPATH, "//a[@href='/sigaa/verPortalCoordenadorGraduacao.do']").click()

     # Ciente
    browser.find_element(By.CSS_SELECTOR, "button.btn.btn-primary").click()

    browser.find_element(By.XPATH, "//span[text() = 'Turmas']").click()

    # Aguardar até que o elemento esteja presente e visível
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, "//*[(text() = 'Consultar Turmas')]")))
    browser.find_element(By.XPATH, "//*[(text() = 'Consultar Turmas')]").click()

    browser.find_element(By.ID, "form:buttonBuscar").click()

    minhasTurmas = ["CCC0741 - COMPILADORES", 
                    "CCC0703 - FUNDAMENTOS MATEMÁTICOS DA COMPUTAÇÃO", 
                    "CCC0730 - INTERAÇÃO HUMANA COM DISPOSITIVOS", 
                    "CCC0719 - PARADIGMAS DE PROGRAMAÇÃO"]

    i = 0

    while True:
        linhas = browser.find_elements(By.XPATH, "//table[@id='lista-turmas']//tbody/tr")

        if i >= len(linhas):
            break

        linha = linhas[i]
        classe = linha.get_attribute("class") or ""

        if "destaque" in classe or "no-hover" in classe:
            i += 1
            continue

        celula = linha.find_element(By.XPATH, ".//td[contains(text(),'alunos')]")

        texto = celula.text.strip()  # "43/60 alunos"

        # pega só a parte antes da barra
        matriculados = int(texto.split("/")[0])

        if matriculados == 0:
            print("Sem alunos, ignorando...")
            i += 1
            continue

        try:
            menu = linha.find_element(By.XPATH, ".//img[contains(@onclick,'exibirOpcoes')]")

            onclick = menu.get_attribute("onclick")
            id_turma = onclick.split("(")[1].split(")")[0]

            disciplina = linha.find_element(
                By.XPATH, "preceding-sibling::tr[contains(@class,'destaque')][1]"
            ).text.strip()

            disciplina = disciplina.split("(")[0].strip()

            print(f"[{i}] Turma ID: {id_turma} | Disciplina: {disciplina} | Matriculados: {matriculados}")

            browser.execute_script("arguments[0].click();", menu)

            menu_tr = WebDriverWait(browser, 10).until(
                EC.visibility_of_element_located((By.ID, f"trOpcoes{id_turma}"))
            )

            botao = menu_tr.find_element(
                By.XPATH, ".//li[@id='btnTurmaVirtual']//a[contains(., 'Visualizar Turma Virtual')]"
            )

            browser.execute_script("arguments[0].click();", botao)

            # 👉 entrou na turma
            wait = WebDriverWait(browser, 10)

            # se a turma for minha, o fluxo é diferente: Diário Eletrônico, depois Mapa de Frequência
            if disciplina in minhasTurmas:
                # Aguarda até que a máscara mude de estado ou suma da tela
                WebDriverWait(browser, 10).until(
                    EC.invisibility_of_element_located((By.ID, "mascara"))
                )
                WebDriverWait(browser, 10).until(
                    EC.element_to_be_clickable((
                        By.XPATH,
                        "//div[contains(@class,'itemMenuHeaderDE') and contains(@class,'-act')]"
                    ))
                ).click()
                WebDriverWait(browser, 10).until(
                    EC.element_to_be_clickable((By.XPATH, "//div[text()='Mapa de Frequência']"))
                ).click()
            else:
                alunos = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'itemMenuHeaderAlunos')]"))
                )
                browser.execute_script("arguments[0].click();", alunos)

                frequencia = wait.until(
                    EC.element_to_be_clickable((By.XPATH, "//div[contains(@class,'itemMenu') and contains(.,'Frequência')]"))
                )
                browser.execute_script("arguments[0].click();", frequencia)

            #esperar o download
            time.sleep(10)

            # depois volta e atualiza a página
            browser.back()
            browser.refresh()

            try:
                WebDriverWait(browser, 3).until(EC.alert_is_present())
                alert = Alert(browser)
                #print("Alerta:", alert.text)
                alert.accept()  # ou alert.dismiss()
            except:
                pass

            # espera a tabela voltar
            wait.until(EC.presence_of_element_located((By.ID, "lista-turmas")))

        except Exception as e:
            print(f"Erro na linha {i}: {e}")

        i += 1
    
    print("Fim...")
    #browser.quit()

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

if __name__ == "__main__":
    # fallback (mantém funcionando standalone)
    config = carregar_configuracoes()
    main()