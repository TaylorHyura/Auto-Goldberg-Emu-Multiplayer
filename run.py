import subprocess
import os
import shutil
import time
import requests
import getpass
import filecmp  # Comparação de arquivos
import tkinter as tk
from tkinter import filedialog

# -----------------------------------
# Configurações Globais
# -----------------------------------
BASE_URL = "https://github.com/Detanup01/gbe_fork/releases/latest/download/"
SEVEN_ZIP_URL = "https://github.com/ip7z/7zip/releases/latest/download/7zr.exe"

SEVEN_ZIP_EXE = "7zr.exe"
FILE_NAMES = ["emu-win-release.7z", "generate_emu_config-win.7z"]
DIRECTORIES_TO_REMOVE = ["parse_controller_vdf", "parse_achievements_schema"]
DIRECTORIES_TO_CHECK = ["generate_emu_config", "release"]
EMU_FOLDER = "Emu"
ASSETS_FILE = "assets.7z"

# Caminhos de login
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGIN_FILE = os.path.join(SCRIPT_DIR, "my_login.txt")
GEN_EMU_LOGIN_FILE = os.path.join("generate_emu_config", "my_login.txt")

# -----------------------------------
# Funções Auxiliares de Arquivo e Diretório
# -----------------------------------

def download_file(url, file_name):
    """Baixa um arquivo de uma URL."""
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"[✔] Download concluído: {file_name}")
    else:
        print(f"[✘] Falha ao baixar {file_name} (Código {response.status_code})")

def extract_file(file_name):
    """Extrai um arquivo compactado usando 7zr.exe."""
    if not os.path.exists(SEVEN_ZIP_EXE):
        print(f"Baixando '{SEVEN_ZIP_EXE}'...")
        download_file(SEVEN_ZIP_URL, SEVEN_ZIP_EXE)

    if os.path.exists(file_name):
        subprocess.run([SEVEN_ZIP_EXE, "x", file_name, "-o."], check=True)
        print(f"[✔] Extração concluída: {file_name}")
        if file_name != ASSETS_FILE:
            os.remove(file_name)
    else:
        print(f"[✘] Erro: '{file_name}' não encontrado!")

def delete_file_or_directory(path):
    """Remove arquivos ou diretórios."""
    if os.path.exists(path):
        shutil.rmtree(path) if os.path.isdir(path) else os.remove(path)
        print(f"[✔] Removido: {path}")

def rename_example_files(directory):
    """Renomeia arquivos/pastas removendo '.EXAMPLE' e '_EXAMPLE'."""
    if os.path.exists(directory):
        for dirpath, dirnames, filenames in os.walk(directory, topdown=False):
            for name in filenames + dirnames:
                new_name = name.replace(".EXAMPLE", "").replace("_EXAMPLE", "")
                if name != new_name:
                    os.rename(os.path.join(dirpath, name), os.path.join(dirpath, new_name))

# -----------------------------------
# Funções de Validação
# -----------------------------------

def is_directory_older_than_7_days(directory):
    """Verifica se uma pasta foi modificada há mais de 7 dias."""
    return os.path.exists(directory) and (time.time() - os.path.getmtime(directory)) / (60 * 60 * 24) > 7

def should_update_directories():
    """Verifica se as pastas precisam ser atualizadas."""
    return any(not os.path.exists(d) or is_directory_older_than_7_days(d) for d in DIRECTORIES_TO_CHECK)

# -----------------------------------
# Funções de Login
# -----------------------------------

def save_login_info():
    """Gerencia login, evitando solicitações desnecessárias."""
    if os.path.exists(LOGIN_FILE) and os.path.exists(GEN_EMU_LOGIN_FILE):
        os.makedirs("generate_emu_config", exist_ok=True)
        shutil.copy(LOGIN_FILE, GEN_EMU_LOGIN_FILE)
        print("[✔] Login copiado para generate_emu_config.")
        return
    elif os.path.exists(LOGIN_FILE):
        if filecmp.cmp(LOGIN_FILE, GEN_EMU_LOGIN_FILE, shallow=False):
            print("[✔] Login já configurado. Nenhuma ação necessária.")
            return

    print("\n--- Login ---")
    username = input("Digite seu nome de usuário: ")
    password = getpass.getpass("Digite sua senha: ")

    with open(LOGIN_FILE, "w") as file:
        file.write(f"{username}\n{password}\n")

    os.makedirs("generate_emu_config", exist_ok=True)
    shutil.copy(LOGIN_FILE, GEN_EMU_LOGIN_FILE)
    print("[✔] Login salvo e copiado para generate_emu_config.")

# -----------------------------------
# Funções de Mesclagem e Movimentação de Pastas
# -----------------------------------

def copy_file(src, dest):
    """Copia um arquivo, substituindo se já existir."""
    shutil.copy2(src, dest)
    print(f"[✔] Copiado: {src} -> {dest}")

def merge_folders(src, dest):
    """Mescla arquivos de uma pasta na outra, substituindo arquivos existentes."""
    if os.path.exists(src):
        os.makedirs(dest, exist_ok=True)
        for item in os.listdir(src):
            s, d = os.path.join(src, item), os.path.join(dest, item)
            if os.path.isdir(s):
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                copy_file(s, d)
    else:
        print(f"[✘] Pasta de origem '{src}' não encontrada!")

def move_steam_settings(appid):
    """Move 'steam_settings' de output para Emu."""
    output_folder, target_folder = os.path.join("output", appid, "steam_settings"), os.path.join(EMU_FOLDER, "steam_settings")

    if os.path.exists(output_folder):
        os.makedirs(target_folder, exist_ok=True)
        merge_folders(output_folder, target_folder)
        print(f"[✔] 'steam_settings' movido para '{EMU_FOLDER}'.")
    else:
        print("[✘] 'steam_settings' não encontrado em output.")

def execute_generate_emu_config(appid):
    """Executa 'generate_emu_config.exe' com o appid."""
    exe_path = os.path.join("generate_emu_config", "generate_emu_config.exe")
    if os.path.exists(exe_path):
        subprocess.run([exe_path, appid], check=True)
    else:
        print(f"[✘] '{exe_path}' não encontrado.")

# -----------------------------------
# Processamento de DLLs
# -----------------------------------

def execute_command(command):
    """Executa um comando no terminal."""
    try:
        subprocess.run(command, check=True)
        print(f"[✔] Comando executado: {' '.join(command)}")
    except subprocess.CalledProcessError:
        print(f"[✘] Erro ao executar: {' '.join(command)}")

def process_dll_file(file_path):
    """Copia o arquivo DLL, executa o comando correspondente e depois renomeia."""
    if not file_path or not file_path.endswith(".dll"):
        print("[✘] Nenhum arquivo válido foi selecionado.")
        return

    file_name = os.path.basename(file_path)
    dest_path = os.path.join(EMU_FOLDER, file_name)
    copy_file(file_path, dest_path)

    if file_name == "steam_api.dll":
        subprocess.run(['release\\tools\\generate_interfaces\\generate_interfaces_x32.exe', dest_path], check=True)
    elif file_name == "steam_api64.dll":
        subprocess.run(['release\\tools\\generate_interfaces\\generate_interfaces_x64.exe', dest_path], check=True)

    new_file_path = dest_path.replace(".dll", "_o.dll")
    os.rename(dest_path, new_file_path)
    print(f"[✔] Arquivo renomeado para '{new_file_path}'.")

# -----------------------------------
# Função Principal
# -----------------------------------

def main():
    if not os.path.exists(EMU_FOLDER):
        if os.path.exists(ASSETS_FILE):
            extract_file(ASSETS_FILE)
            delete_file_or_directory(SEVEN_ZIP_EXE)
        else:
            print(f"[✘] '{ASSETS_FILE}' não encontrado!")
            return

    if should_update_directories():
        print("Atualizando pastas...")

        for directory in DIRECTORIES_TO_CHECK:
            delete_file_or_directory(directory)

        for file_name in FILE_NAMES:
            download_file(BASE_URL + file_name, file_name)
            extract_file(file_name)

        delete_file_or_directory(SEVEN_ZIP_EXE)
        for directory in DIRECTORIES_TO_REMOVE:
            delete_file_or_directory(directory)

        for directory in DIRECTORIES_TO_CHECK:
            rename_example_files(directory)

    save_login_info()
    appid = input("Por favor, insira o 'appid': ")
    execute_generate_emu_config(appid)
    move_steam_settings(appid)
    delete_file_or_directory("output")

    root = tk.Tk()
    root.withdraw()
    file_path = filedialog.askopenfilename(title="Selecione steam_api.dll ou steam_api64.dll", filetypes=[("DLL files", "*.dll")])
    process_dll_file(file_path)

    input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()