import subprocess
import sys
import time

# Lista dos seus scripts na ordem exata de execução
scripts = [
            "1-ExtraiDiariosDoSIGAA_CCO.py",
            "2-MoverHistoricos.py",
            "3-ExtrairFaltasDosPDFs.py", 
            "4-Delete_upload_to_supabase.py"
            ]

for script in scripts:
    print(f"\n--- Iniciando: {script} ---")
    inicio = time.time()
    
    try:
        # check=True faz o Python disparar um erro se o script falhar
        subprocess.run([sys.executable, script], check=True)
        
        fim = time.time()
        print(f"--- Sucesso: {script} finalizado em {fim - inicio:.2f}s ---")

        '''
        # se y continuar para o próximo script
        choice = input("Pressione 'y' para continuar para o próximo script ou qualquer outra tecla para sair: ")
        if choice.lower() != 'y':
            print("Interrompendo a sequência de scripts.")
            sys.exit(0)
        '''
        
    except subprocess.CalledProcessError as e:
        print(f"\n[ERRO FATA] O {script} falhou. Interrompendo a sequência.")
        sys.exit(1)

print("\nProcesso completo executado com sucesso!")