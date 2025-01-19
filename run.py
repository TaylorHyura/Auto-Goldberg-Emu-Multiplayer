import subprocess
import os
import shutil
import time
import requests
import getpass  # Ocultar entrada da senha

# URLs e nomes dos arquivos
BASE_URL = "https://github.com/Detanup01/gbe_fork/releases/latest/download/"
SEVEN_ZIP_URL = "https://github.com/ip7z/7zip/releases/latest/download/7zr.exe"

SEVEN_ZIP_EXE = "7zr.exe"
FILE_NAMES = ["emu-win-release.7z", "generate_emu_config-win.7z"]
DIRECTORIES_TO_REMOVE = ["parse_controller_vdf", "parse_achievements_schema"]
DIRECTORIES_TO_CHECK = ["generate_emu_config", "release"]
EMU_FOLDER = "Emu"
ASSETS_FILE = "assets.7z"
LOGIN_FILE = os.path.join("generate_emu_config", "my_login.txt")

# -----------------------------------
# Funções Auxiliares de Arquivo e Diretório
# -----------------------------------

def download_file(url, file_name):
    """Baixa um arquivo de uma URL especificada."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"Download concluído: {file_name}")
    else:
        print(f"Falha ao baixar {file_name}: Código {response.status_code}")

def extract_file(file_name):
    """Extrai um arquivo compactado usando 7zr.exe."""
    if not os.path.exists(SEVEN_ZIP_EXE):
        print(f"Baixando '{SEVEN_ZIP_EXE}'...")
        download_file(SEVEN_ZIP_URL, SEVEN_ZIP_EXE)

    if os.path.exists(file_name):
        subprocess.run([SEVEN_ZIP_EXE, "x", file_name, "-o."], check=True)
        print(f"Extração concluída: {file_name}")
        if file_name != ASSETS_FILE:  # Mantém assets.7z, remove outros
            os.remove(file_name)
            print(f"Arquivo removido após extração: {file_name}")
    else:
        print(f"Erro: '{file_name}' não encontrado!")

def delete_file_or_directory(path):
    """Remove arquivos ou diretórios."""
    if os.path.exists(path):
        if os.path.isdir(path):
            shutil.rmtree(path, ignore_errors=True)
        else:
            os.remove(path)
        print(f"Removido: {path}")

def remove_example_name(path):
    """Renomeia arquivos e pastas removendo sufixos '.EXAMPLE' ou '_EXAMPLE'."""
    if os.path.exists(path):
        for dirpath, dirnames, filenames in os.walk(path, topdown=False):
            for filename in filenames:
                new_name = filename.replace(".EXAMPLE", "").replace("_EXAMPLE", "")
                if filename != new_name:
                    os.rename(os.path.join(dirpath, filename), os.path.join(dirpath, new_name))
            for dirname in dirnames:
                new_name = dirname.replace(".EXAMPLE", "").replace("_EXAMPLE", "")
                if dirname != new_name:
                    os.rename(os.path.join(dirpath, dirname), os.path.join(dirpath, new_name))

# -----------------------------------
# Funções de Diretórios e Validações
# -----------------------------------

def check_if_directory_older_than_7_days(directory):
    """Verifica se a pasta foi modificada há mais de 7 dias."""
    if os.path.exists(directory):
        last_modified_time = os.path.getmtime(directory)
        return (time.time() - last_modified_time) / (60 * 60 * 24) > 7
    return False

def should_update_directories():
    """Verifica se é necessário atualizar os diretórios, com base na data ou existência."""
    for directory in DIRECTORIES_TO_CHECK:
        if not os.path.exists(directory) or check_if_directory_older_than_7_days(directory):
            return True
    return False

# -----------------------------------
# Funções de Entrada de Dados
# -----------------------------------

def get_appid():
    """Solicita e valida o appid do usuário."""
    while True:
        appid = input("Por favor, insira o 'appid': ")
        if appid.isdigit():
            return appid
        else:
            print("Por favor, insira um appid válido (apenas números).")

def save_login_info():
    """Solicita nome de usuário e senha e salva em my_login.txt."""
    print("\n--- Login ---")
    username = input("Digite seu nome de usuário: ")
    password = getpass.getpass("Digite sua senha: ")  # Oculta a entrada da senha

    os.makedirs("generate_emu_config", exist_ok=True)
    with open(LOGIN_FILE, "w") as file:
        file.write(f"{username}\n")
        file.write(f"{password}\n")
    print(f"Login salvo em: {LOGIN_FILE}")

# -----------------------------------
# Funções de Mesclagem e Movimentação de Pastas
# -----------------------------------

def merge_folders(src_folder, dest_folder):
    """Mescla os arquivos de uma pasta na outra, substituindo os arquivos existentes."""
    if os.path.exists(src_folder):
        for item in os.listdir(src_folder):
            s = os.path.join(src_folder, item)
            d = os.path.join(dest_folder, item)
            if os.path.isdir(s):
                if not os.path.exists(d):
                    shutil.copytree(s, d)
                else:
                    merge_folders(s, d)  # Mescla recursivamente
            else:
                shutil.copy2(s, d)  # Substitui o arquivo existente
                print(f"Arquivo '{s}' substituído por '{d}'")
    else:
        print(f"A pasta de origem '{src_folder}' não foi encontrada!")

def move_steam_settings(appid):
    """Move a pasta steam_settings de 'output' para 'Emu', substituindo os arquivos existentes."""
    output_folder = os.path.join("output", appid, "steam_settings")
    target_folder = os.path.join(EMU_FOLDER, "steam_settings")

    if os.path.exists(output_folder):
        if os.path.exists(target_folder):
            print(f"Mesclando pasta 'steam_settings' de '{output_folder}' para '{target_folder}'...")
            merge_folders(output_folder, target_folder)
        else:
            shutil.move(output_folder, target_folder)
            print(f"Pasta 'steam_settings' movida para '{EMU_FOLDER}'.")
    else:
        print("Pasta 'steam_settings' não encontrada dentro de 'output'.")

def execute_generate_emu_config(appid):
    """Executa o 'generate_emu_config.exe' com o appid fornecido."""
    generate_emu_config_path = os.path.join("generate_emu_config", "generate_emu_config.exe")
    if os.path.exists(generate_emu_config_path):
        subprocess.run([generate_emu_config_path, appid], check=True)
        print(f"Comando executado com o appid: {appid}")
    else:
        print(f"Erro: {generate_emu_config_path} não encontrado.")

# -----------------------------------
# Função Principal
# -----------------------------------

def main():
    # Se a pasta "Emu" não existe, extraímos "assets.7z"
    if not os.path.exists(EMU_FOLDER):
        print(f"A pasta '{EMU_FOLDER}' não existe. Extraindo '{ASSETS_FILE}'...")
        if os.path.exists(ASSETS_FILE):
            extract_file(ASSETS_FILE)
            delete_file_or_directory(SEVEN_ZIP_EXE)
        else:
            print(f"Erro: '{ASSETS_FILE}' não encontrado na pasta do script!")
            return

    # Verifica se é necessário atualizar diretórios
    if should_update_directories():
        print("Atualizando pastas. Procedendo com download e extração.")

        # Excluir pastas antigas
        for directory in DIRECTORIES_TO_CHECK:
            delete_file_or_directory(directory)

        # Baixar e extrair arquivos principais
        for file_name in FILE_NAMES:
            download_file(BASE_URL + file_name, file_name)
            extract_file(file_name)

        # Limpeza após uso
        delete_file_or_directory(SEVEN_ZIP_EXE)
        for directory in DIRECTORIES_TO_REMOVE:
            delete_file_or_directory(directory)

        # Remover ".EXAMPLE" e "_EXAMPLE"
        for directory in DIRECTORIES_TO_CHECK:
            remove_example_name(directory)
    else:
        print("As pastas estão atualizadas. Nenhuma ação necessária.")

    # Solicita e salva o login
    save_login_info()

    # Solicita o appid e executa o comando
    appid = get_appid()
    execute_generate_emu_config(appid)

    # Mescla ou move a pasta 'steam_settings'
    move_steam_settings(appid)

    # Remove a pasta 'output'
    delete_file_or_directory("output")

    input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()