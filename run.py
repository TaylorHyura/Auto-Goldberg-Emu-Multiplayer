import subprocess # Execução de comandos
import os # Manipulação de arquivos
import shutil
import time # Manipulação de tempo
import requests # Requisições HTTP
import getpass # Ocultar senha
import filecmp # Comparação de arquivos
import tkinter as tk # Interface gráfica
from tkinter import filedialog 

# -----------------------------------
# Configurações Globais
# -----------------------------------
GBE_URL = "https://github.com/Detanup01/gbe_fork/releases/latest/download/"
SEVEN_ZIP_URL = "https://github.com/ip7z/7zip/releases/latest/download/7zr.exe"

SEVEN_ZIP_EXE = "7zr.exe"
ASSETS_FILE = "assets.7z"
GBE_FILES = ["emu-win-release.7z", "generate_emu_config-win.7z"]

FOLDES_TO_REMOVE = ["parse_controller_vdf", "parse_achievements_schema"]
FOLDES_TO_CHECK = ["generate_emu_config", "release"]
EMU_FOLDER = "Emu"
EMU_STEAM_SETTINGS = os.path.join(EMU_FOLDER, "steam_settings")

STEAM_API32_FILE = "release\\experimental\\x32\\steam_api.dll"
STEAM_API64_FILE = "release\\experimental\\x64\\steam_api64.dll"
GBE_STEAM_SETTINGS = "release\\steam_settings"
STEAM_INTERFACES_FILE = "steam_interfaces.txt"
CONFIGS_OVERLAY_FILE = "configs.overlay.ini"
CUSTOM_BROADCASTS_FILE = "custom_broadcasts.txt"

# Caminhos de login
LOGIN_FILE = "my_login.txt"
GEN_EMU_LOGIN_FILE = os.path.join("generate_emu_config", LOGIN_FILE)

# -----------------------------------
# Funções Auxiliares de Arquivo e Diretório
# -----------------------------------

def download_file(url, file_name):
    """Baixa arquivos atraves uma URL."""
    print(f"Baixando {file_name}...")
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(file_name, "wb") as file:
            for chunk in response.iter_content(1024):
                file.write(chunk)
        print(f"[✔] Download concluído: {file_name}")
    else:
        print(f"[✘] Falha ao baixar: {file_name} (Código {response.status_code})")

def ensure_seven_zip():
    """Baixa o 7zr.exe se não existir."""
    if not os.path.exists(SEVEN_ZIP_EXE):
        download_file(SEVEN_ZIP_URL, SEVEN_ZIP_EXE)

def extract_file(file_name):
    """Extrai arquivos usando 7zr.exe."""
    print(f"Extraindo {file_name}...")
    if os.path.exists(file_name):
        subprocess.run([SEVEN_ZIP_EXE, "x", file_name, "-o."], check=True)
        print(f"[✔] Extração concluída: {file_name}")
        #if file_name != ASSETS_FILE:
        #    delete_file_or_directory(file_name)
    else:
        print(f"[✘] Falha ao extrair: {file_name} não encontrado!")

def delete_file_or_directory(path):
    """Remove arquivos ou diretórios."""
    if os.path.exists(path):
        print(f"Removendo {path}...")
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
    return any(not os.path.exists(d) or is_directory_older_than_7_days(d) for d in FOLDES_TO_CHECK)

# -----------------------------------
# Funções de Login
# -----------------------------------

def save_login_info():
    """Gerencia login, evitando solicitações desnecessárias."""
    if os.path.exists(LOGIN_FILE):
        if filecmp.cmp(LOGIN_FILE, GEN_EMU_LOGIN_FILE, shallow=False):
            print("[✔] Login já configurado. Nenhuma ação necessária.")
            return
        else:
            shutil.copy(LOGIN_FILE, GEN_EMU_LOGIN_FILE)
            print("[✔] Login copiado para generate_emu_config.")
            return
        
    print("\n--- Login Steam---")
    username = input("Digite seu nome: ")
    password = getpass.getpass("Digite sua senha: ")

    with open(LOGIN_FILE, "w") as file:
        file.write(f"{username}\n{password}\n")

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
        print(f"[✘] Pasta {src} não encontrada!")

def move_steam_settings(appid):
    """Move 'steam_settings' de output para Emu."""
    output_folder, target_folder = os.path.join("output", appid, "steam_settings"), EMU_STEAM_SETTINGS

    merge_folders(output_folder, target_folder)

def execute_generate_emu_config(appid):
    """Executa 'generate_emu_config.exe' com o appid."""
    exe_path = "generate_emu_config\\generate_emu_config.exe"
    if os.path.exists(exe_path):
        subprocess.run([exe_path, appid], check=True)
    else:
        print(f"[✘] {exe_path} não encontrado.")

# -----------------------------------
# Processamento de fisheiros
# -----------------------------------

def process_steamapi_files():
    """Copia o arquivo 'steam_api.dll' do jogo, executa o comando para obter 'steam_interfaces.txt', faz backup alterando o nome e copia o 'steam_api.dll' do emu."""
    root = tk.Tk()
    root.withdraw()
    print("Selecione steam_api.dll ou steam_api64.dll.")
    file_path = filedialog.askopenfilename(title="Selecione steam_api.dll ou steam_api64.dll", filetypes=[("DLL files", "*.dll")])
    
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
    print(f"[✔] Renomeado: {dest_path} -> {new_file_path}")

    emu_steam_interfaces = os.path.join(EMU_STEAM_SETTINGS, STEAM_INTERFACES_FILE)

    shutil.move(STEAM_INTERFACES_FILE, emu_steam_interfaces)
    print(f"[✔] Movido: {STEAM_INTERFACES_FILE} -> {emu_steam_interfaces}")

    copy_file(STEAM_API64_FILE if "64" in file_name else STEAM_API32_FILE, os.path.join(EMU_FOLDER, file_name))

def process_configs_overlay():
    """Copia o arquivo 'configs.overlay.ini' e faz a alteração do campo 'enable_experimental_overlay'."""
    gbe_configs_overlay = os.path.join(GBE_STEAM_SETTINGS, CONFIGS_OVERLAY_FILE)
    emu_configs_overlay = os.path.join(EMU_STEAM_SETTINGS, CONFIGS_OVERLAY_FILE)

    copy_file(gbe_configs_overlay, emu_configs_overlay)

    with open(emu_configs_overlay, "r", encoding="utf-8") as file:
        lines = file.readlines()

    with open(emu_configs_overlay, "w", encoding="utf-8") as file:
        for line in lines:
            if line.strip().startswith("enable_experimental_overlay="):
                file.write("enable_experimental_overlay=1\n")
            else:
                file.write(line)

def process_custom_broadcasts():
    """Copia o arquivo 'custom_broadcasts.txt'."""
    gbe_custom_broadcasts = os.path.join(GBE_STEAM_SETTINGS, CUSTOM_BROADCASTS_FILE)
    emu_custom_broadcasts = os.path.join(EMU_STEAM_SETTINGS, CUSTOM_BROADCASTS_FILE)

    copy_file(gbe_custom_broadcasts, emu_custom_broadcasts)

    try:
        response = requests.get("https://api64.ipify.org?format=text", timeout=5)
        response.raise_for_status()

        ip_publico = response.text

        with open(emu_custom_broadcasts, "w", encoding="utf-8") as f:
            f.write(ip_publico)  
    except requests.RequestException as e:
        print(f"[✘] Falha ao obter IP público: {e}")

# -----------------------------------
# Função Principal
# -----------------------------------

def main():
    """Fluxo principal do script."""
    ensure_seven_zip()

    if os.path.exists(EMU_FOLDER):
        delete_file_or_directory(EMU_FOLDER)
    
    if not os.path.exists(ASSETS_FILE):
        print(f"[✘] {ASSETS_FILE} não encontrado!")
        return
    
    extract_file(ASSETS_FILE)

    if should_update_directories():
        print("Atualizando pastas e ficheiro...")

        delete_file_or_directory(SEVEN_ZIP_EXE)
        ensure_seven_zip()

        for directory in FOLDES_TO_CHECK:
            delete_file_or_directory(directory)

        for file in GBE_FILES:
            download_file(GBE_URL + file, file)
            extract_file(file)

        for directory in FOLDES_TO_REMOVE:
            delete_file_or_directory(directory)

        for directory in FOLDES_TO_CHECK:
            rename_example_files(directory)

    save_login_info()
    appid = input("Por favor, insira o 'appid': ")
    execute_generate_emu_config(appid)

    move_steam_settings(appid)
    delete_file_or_directory("output")
    process_steamapi_files()
    process_configs_overlay()
    process_custom_broadcasts()

    input("Pressione Enter para sair...")

if __name__ == "__main__":
    main()