import glob
import os
import shutil
import os

# __file__ é o arquivo atual. abspath pega o caminho completo e dirname pega a pasta.
pasta_do_script = os.path.dirname(os.path.abspath(__file__))

# Defina os caminhos das pastas
# O '~' representa a pasta raiz do usuário (ex: C:\Users\NomeDoUsuario)
caminho_usuario = os.path.expanduser("~")

# Junta a pasta do usuário com a pasta "Downloads"
pasta_downloads = os.path.join(caminho_usuario, "Downloads")

# juntar pasta_do_script com diretório pdf
pasta_destino = os.path.join(pasta_do_script, "pdfs")

print(f"O caminho completo é: {pasta_destino}")

# Garante que a pasta de destino exista
os.makedirs(pasta_destino, exist_ok=True)

# Cria o padrão de busca: arquivos que começam com "mapa_" e terminam com ".pdf"
# O asterisco (*) funciona como um coringa para qualquer caractere no meio
padrao_busca = os.path.join(pasta_downloads, "mapa_*_.pdf")

# O glob.glob encontra todos os arquivos que se encaixam perfeitamente no padrão
arquivos_encontrados = glob.glob(padrao_busca)

# Move cada arquivo encontrado
for caminho_origem in arquivos_encontrados:
    # Extrai apenas o nome do arquivo (ex: mapa_CCC0702_2026.2_01_.pdf)
    nome_arquivo = os.path.basename(caminho_origem)
    
    caminho_destino = os.path.join(pasta_destino, nome_arquivo)
    
    # Move para o destino
    shutil.move(caminho_origem, caminho_destino)

    print(f"Movido com sucesso: {nome_arquivo}")
