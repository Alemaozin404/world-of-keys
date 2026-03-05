import os
import json
import re
from pathlib import Path
from datetime import datetime

class KeyManager:
    def __init__(self):
        self.keys = {}
        self.config_file = "keys_database.json"
        self.load_keys()
    
    def load_keys(self):
        if os.path.exists(self.config_file):
            with open(self.config_file, 'r', encoding='utf-8') as f:
                self.keys = json.load(f)
    
    def save_keys(self):
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.keys, f, indent=4, ensure_ascii=False)
    
    def scan_env_files(self, directory='.'):
        env_patterns = ['.env', '.env.local', '.env.production', 'config.env']
        found_keys = {}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file in env_patterns or file.endswith('.env'):
                    filepath = os.path.join(root, file)
                    found_keys.update(self.extract_from_env(filepath))
        
        return found_keys
    
    def extract_from_env(self, filepath):
        keys = {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        match = re.match(r'([A-Z_][A-Z0-9_]*)\s*=\s*(.+)', line)
                        if match:
                            key_name = match.group(1)
                            key_value = match.group(2).strip('"\'')
                            keys[key_name] = {
                                'value': key_value,
                                'source': filepath,
                                'found_at': datetime.now().isoformat()
                            }
        except Exception as e:
            print(f"Erro ao ler {filepath}: {e}")
        
        return keys
    
    def scan_config_files(self, directory='.'):
        config_patterns = ['config.json', 'config.js', 'settings.json']
        found_keys = {}
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                if file in config_patterns:
                    filepath = os.path.join(root, file)
                    if file.endswith('.json'):
                        found_keys.update(self.extract_from_json(filepath))
        
        return found_keys
    
    def extract_from_json(self, filepath):
        keys = {}
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
                keys.update(self.find_keys_in_dict(data, filepath))
        except Exception as e:
            print(f"Erro ao ler {filepath}: {e}")
        
        return keys
    
    def find_keys_in_dict(self, data, source, prefix=''):
        keys = {}
        key_patterns = ['key', 'token', 'secret', 'api', 'password', 'auth']
        
        if isinstance(data, dict):
            for k, v in data.items():
                current_key = f"{prefix}.{k}" if prefix else k
                if any(pattern in k.lower() for pattern in key_patterns):
                    if isinstance(v, str):
                        keys[current_key] = {
                            'value': v,
                            'source': source,
                            'found_at': datetime.now().isoformat()
                        }
                elif isinstance(v, (dict, list)):
                    keys.update(self.find_keys_in_dict(v, source, current_key))
        elif isinstance(data, list):
            for i, item in enumerate(data):
                keys.update(self.find_keys_in_dict(item, source, f"{prefix}[{i}]"))
        
        return keys
    
    def add_key(self, site_name, key_name, key_value):
        if site_name not in self.keys:
            self.keys[site_name] = {}
        
        self.keys[site_name][key_name] = {
            'value': key_value,
            'added_at': datetime.now().isoformat()
        }
        self.save_keys()
    
    def get_key(self, site_name, key_name=None):
        if site_name in self.keys:
            if key_name:
                return self.keys[site_name].get(key_name)
            return self.keys[site_name]
        return None
    
    def list_all(self):
        return self.keys
    
    def export_to_file(self, filename='keys_export.json'):
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.keys, f, indent=4, ensure_ascii=False)
        print(f"Keys exportadas para {filename}")

def main():
    manager = KeyManager()
    
    print("=" * 50)
    print("SOFTWARE DE RESGATE DE KEYS")
    print("=" * 50)
    
    while True:
        print("\n[1] Escanear diretório por arquivos .env")
        print("[2] Escanear diretório por arquivos de configuração")
        print("[3] Adicionar key manualmente")
        print("[4] Ver key específica")
        print("[5] Listar todas as keys")
        print("[6] Exportar keys para arquivo")
        print("[7] Sair")
        
        opcao = input("\nEscolha uma opção: ").strip()
        
        if opcao == '1':
            path = input("Digite o caminho do diretório (ou Enter para diretório atual): ").strip()
            if not path:
                path = '.'
            print("\nEscaneando arquivos .env...")
            found = manager.scan_env_files(path)
            if found:
                print(f"\n{len(found)} keys encontradas:")
                for key, data in found.items():
                    print(f"  {key}: {data['value'][:20]}... (fonte: {data['source']})")
                    manager.keys[data['source']] = manager.keys.get(data['source'], {})
                    manager.keys[data['source']][key] = data
                manager.save_keys()
            else:
                print("Nenhuma key encontrada.")
        
        elif opcao == '2':
            path = input("Digite o caminho do diretório (ou Enter para diretório atual): ").strip()
            if not path:
                path = '.'
            print("\nEscaneando arquivos de configuração...")
            found = manager.scan_config_files(path)
            if found:
                print(f"\n{len(found)} keys encontradas:")
                for key, data in found.items():
                    print(f"  {key}: {data['value'][:20]}... (fonte: {data['source']})")
                    manager.keys[data['source']] = manager.keys.get(data['source'], {})
                    manager.keys[data['source']][key] = data
                manager.save_keys()
            else:
                print("Nenhuma key encontrada.")
        
        elif opcao == '3':
            site = input("Nome do site/serviço: ").strip()
            key_name = input("Nome da key: ").strip()
            key_value = input("Valor da key: ").strip()
            manager.add_key(site, key_name, key_value)
            print("Key adicionada com sucesso!")
        
        elif opcao == '4':
            site = input("Nome do site/serviço: ").strip()
            key_name = input("Nome da key (ou Enter para todas): ").strip()
            if key_name:
                result = manager.get_key(site, key_name)
            else:
                result = manager.get_key(site)
            
            if result:
                print("\nResultado:")
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                print("Key não encontrada.")
        
        elif opcao == '5':
            all_keys = manager.list_all()
            if all_keys:
                print("\nTodas as keys armazenadas:")
                print(json.dumps(all_keys, indent=2, ensure_ascii=False))
            else:
                print("Nenhuma key armazenada.")
        
        elif opcao == '6':
            filename = input("Nome do arquivo (ou Enter para 'keys_export.json'): ").strip()
            if not filename:
                filename = 'keys_export.json'
            manager.export_to_file(filename)
        
        elif opcao == '7':
            print("Saindo...")
            break
        
        else:
            print("Opção inválida!")

if __name__ == "__main__":
    main()
