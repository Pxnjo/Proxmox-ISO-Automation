import urllib.parse # Permette di convertire i caratteri speciali in URL
import requests # Permette di fare richieste HTTP
import paramiko # Permette di fare connessioni SSH
import logging # permette di fare i log
import urllib3 # Permette di disabilitare i warning per i certificati non validi
import time # Permette di fare pause
import json # Permette di manipolare file json
import sys, re, os

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning) # Disabilita i warning per i certificati non validi
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), ".")))
script_dir = os.path.dirname(os.path.abspath(__file__))  # Ottiene la cartella dello script
private_key_path = os.path.join(script_dir, 'id_ed25519')  # Crea il percorso corretto
public_key_path = os.path.join(script_dir, 'id_ed25519.pub')  # Crea il percorso corretto
# Percorso della cartella logs
log_dir = os.path.join(script_dir, "logs")
# Assicurati che la cartella logs esista
os.makedirs(log_dir, exist_ok=True)

ip_addr = ''
vmid = 0
def main():
    global vmid
    from config import node, server, gateway, templateID, API_TOKEN ,hostname
    headers = {
        'Authorization': API_TOKEN,
        'Content-Type': 'application/json'
    }
    # Dichiarazione variabili globali
    base_url = f"https://{server}:8006/api2/json/nodes/{node}"
    with open(public_key_path, "r") as file: # legge la chiave pubblica
        public_key = file.read().strip()

    client = paramiko.SSHClient() # initializza la connessione SSH

    # Gestione errori
    def describe_errors(response):
        return response.status_code, response.text
    # Dichiarazone metodi API
    def metodo(type, url, headers, data=None):
                if type == 'get':
                    response = requests.get(url, headers=headers, verify=False)
                elif type == 'post':
                    response = requests.post(url, headers=headers, json=data, verify=False)
                elif type == 'put':
                    response = requests.put(url, headers=headers, json=data, verify=False)
                elif type == 'delete':
                    response = requests.delete(url, headers=headers, verify=False)
                return response

    # Clone VM from template
    def clone_vm(templateId):
        # Get first unsed VMid
        global vmid
        vmid = 100 # VMID di partenza
        url = f"{base_url}/qemu"
        response = metodo('get', url, headers)
        if response.status_code == 200:
            vm_list = response.json()['data']
            vm_ids = [vm['vmid'] for vm in vm_list if vm['vmid']]
        else:
            print(f"Error to retrieve vmid: {describe_errors(response)}")

        while vmid in vm_ids:  # Se vmid è già nella lista, incrementalo
            vmid += 1
        # Clone VM
        url = f"{base_url}/qemu/{templateId}/clone"
        data = {
            "newid": vmid, # VMid della nuova macchina
            
        }
        response = metodo('post', url, headers, data)
        if response.status_code == 200:
            print(f"VM {vmid} cloned successfully")
            return vmid
        else:
            print(f"VM clone failed: {describe_errors(response)}")
            return
    def check_if_cloned(vmid):
        url = f"{base_url}/qemu/{vmid}/status/current"
        attempt = 0
        while attempt < 3:
            response = metodo('get', url, headers)
            if response.status_code == 200:
                return True
            else:
                time.sleep(10)
                attempt += 1
        return False

    #Resize disk
    def resize_disk(check_if_cloned): #si assicura che la macchina sia clonata prima di fare il resize del disk
        if check_if_cloned is not None:
            data = {
                "disk": "scsi0",
                "size": "+5G"
            }
            url = f"{base_url}/qemu/{vmid}/resize"
            response = metodo('put', url, headers, data)
            if response.status_code == 200:
                print(f"Disk resized successfully\n|-- Disk: {data['disk']}\n|-- Size: {data['size']}")
            else:
                print(f"Disk resize failed: {describe_errors(response)}")

    #Configure Cloudinit
    def cloud_init(i, ip=None):
        if i == 0:
            ciuser = 'test'
            ipconfig0 = "DHCP"
            data = {
                "ciuser": "test",
                "cipassword": "Vmware1!",
                "sshkeys": public_key,
                "ipconfig0": "ip=dhcp",
                "searchdomain": "8.8.8.8",
                "nameserver": "8.8.4.4"
            }
        elif i == 1:
            ciuser = 'root'
            ipconfig0 = f"ip={ip}/8,gw={gateway}"
            data = {
                "ciuser": "root",
                "cipassword": "Vmware1!",
                "sshkeys": public_key,
                "ipconfig0": ipconfig0,
                "searchdomain": "8.8.8.8",
                "nameserver": "8.8.4.4"
            }
        else:
            print("Valore di 'i' non valido. Usa 0 o 1.")
            return  # Esce dalla funzione se i non è né 0 né 1
        
        # Codifica la chiave SSH per l'URL
        data["sshkeys"] = urllib.parse.quote(data["sshkeys"])

        # Invio della richiesta API
        url = f"{base_url}/qemu/{vmid}/config"
        response = metodo('put', url, headers, data)

        # Controllo del risultato
        if response.status_code == 200:
            print(f"Cloudinit configured successfully\n|-- User: {ciuser}\n|-- Password: Vmware1!\n|-- Dns domain: {data['searchdomain']}\n|-- Nameserver: {data['nameserver']}\n|-- Sshkey: {public_key}\n|-- Ip: {ipconfig0}")
            i += 1
            return True, ciuser
        else:
            print(f"Cloudinit configuration failed: {describe_errors(response)}")

    #delete efi disk
    def delete_efi_disk():
        data = {
            "delete":"efidisk0"
        }
        url = f"{base_url}/qemu/{vmid}/config"
        response = metodo('put', url, headers, data)
        if response.status_code == 200:
            print(f"EFI disk delete successfully")
        else:
            print(f"EFI disk delete failed: {describe_errors(response)}")

    # set hostname
    def set_hostname():
        data = {
            "name": hostname
        }
        url = f"{base_url}/qemu/{vmid}/config"
        response = metodo('put', url, headers, data)
        if response.status_code == 200:
            print(f"Hostname set successfully: {data['name']}")
            return data['name']
        else:
            print(f"Hostname set failed: {describe_errors(response)}")

    def check_xterm_js():
        url = f"{base_url}/qemu/{vmid}/config"
        response = metodo('get', url, headers)
        status = response.json()['data']
        if 'serial0' in status:
            print(f"Xterm.js serial port found: {response.json()['data']['serial0']}")
        else:
            print(f"Xterm.js serial port not found")

    # Start VM
    def start_vm():
        url = f"{base_url}/qemu/{vmid}/status/start"
        response = metodo('post',  url, headers, data={}) # proxmox si aspetta un json anche se vuoto
        if response.status_code == 200:
            print(f"VM {vmid} started successfully")
        else:
            print(f"VM {vmid} start failed: {describe_errors(response)}")

    # Get VM IP
    def get_IPvm(boot_counter = None, timeout=120):
        global ip_addr # variabile temporanea al posto del dhcp
        start_time = time.time()  # Registra l'ora di inizio
        print("Waiting for VM IP...")
        while True:
            if time.time() - start_time > timeout: # timeout se non trova l'ip
                    print("Unable to get VM IP after 2min")
                    if boot_counter == 0:
                        return 1 # se era il primo tentativo di boot in uefi allora ritorna 1 per impostare il boot in bios
                    else:
                        return 2 # se nemmeno al secondo tentativo non funziona allora la macchina non parte
            url = f"{base_url}/qemu/{vmid}/agent/network-get-interfaces"
            response = metodo('get', url, headers)
            if response.status_code == 200:
                json_data = response.json()
                interfaces = json_data.get('data', {}).get('result', [])
                if len(interfaces) < 2: # Se le interfacce sono minori di 2 vuol dire che è presente solo quella di loopback
                    time.sleep(10)
                for item in interfaces:
                    if 'lo' in item.get('name', '') or not item.get('ip-addresses', []) : # Se 'lo' o la scritta ip-addresses non esiste riprova
                        time.sleep(5)
                        continue
                    else: 
                        for search_ipv4 in item.get('ip-addresses', []): # Se ip-addresses esiste ma l'ipè vuoto riprova
                            if search_ipv4.get('ip-address-type') != 'ipv4': # Se ip-addresses esiste ma l'ip è vuoto riprova
                                time.sleep(5)
                                continue
                            else:
                                ip_addr = response.json()['data']['result'][1]['ip-addresses'][0]['ip-address']
                                print(f'L\'ip della nuova VM è: {ip_addr}')
                                return ip_addr # se ottengo l'ip address vuol dire che la macchina parte
            else:
                time.sleep(5)

    # set Boot mode in BIOS
    def set_boot_mode(boot_counter):
        if boot_counter == 0:
            bios = 'UEFI'
            data = {
                "bios": "ovmf"
            }
        else:
            bios = 'BIOS'
            data = {
                "bios": "seabios"
            }
        url = f"{base_url}/qemu/{vmid}/config"
        response = metodo('put', url, headers, data)
        if response.status_code == 200:
            print(f"Boot mode set to {bios} successfully")
            return bios
        else:
            print(f"Boot mode set to {bios} failed: {describe_errors(response)}")

    # SSH connection
    def ssh():
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #Accetta la chiave pubblica del server se non presente nel known_hosts
        hostname = ip_addr
        print(f"Trying to connect to {hostname}")
        port = 22
        username = user
        print(f"Trying to connect with user '{username}'")
        password = 'Vmware1!'
        max_retries = 5  # Numero massimo di tentativi
        attempt = 0  # Contatore dei tentativi
        while attempt < max_retries:
            try:
                client.connect(hostname, port=port, username=username, password=password)
                stdin, stdout, stderr = client.exec_command('whoami')
                output = stdout.read().decode('utf-8').strip()
                print(f"User '{output}' logged in successfully with password") # il print verrà eseguito solo se la connessione ssh riesce perchè il try in caso di errore passa direttamente dal except
                break
            except paramiko.ssh_exception.AuthenticationException as auth_error:
                print(f"- User '{username}' authentication with password failed: {auth_error}")
                break
            except paramiko.ssh_exception.SSHException as ssh_error:
                print(f"SSH error: {ssh_error}")
            except Exception as e:
                pass
            attempt += 1
            time.sleep(10)
        else:
            print(f"Failed to connect with user ' {user}' and password to {hostname} after {max_retries} attempts")
        client.close()
        client.get_host_keys().clear()

    # SSH connection with private key
    def ssh_key():
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy()) #Accetta la chiave pubblica del server se non presente nel known_hosts
        hostname = ip_addr
        port = 22
        username = user
        max_retries = 5  # Numero massimo di tentativi
        attempt = 0  # Contatore dei tentativi
        while attempt < max_retries:
            try:
                client.connect(hostname, port=port, username=username, key_filename=private_key_path)
                stdin, stdout, stderr = client.exec_command('whoami')
                output = stdout.read().decode('utf-8').strip()
                print(f"User '{output}' logged in successfully with the key") # il print verrà eseguito solo se la connessione ssh riesce perchè il try in caso di errore passa direttamente dal except
                break
            except paramiko.ssh_exception.AuthenticationException as auth_error:
                print(f"User '{username}' authentication failed: {auth_error}")
                break
            except paramiko.ssh_exception.SSHException as ssh_error:
                print(f"SSH error: {ssh_error}")
            except Exception as e:
                pass
            attempt += 1
            time.sleep(10)
        else: 
            print(f"Failed to connect with '{user}' and key to {hostname} after {max_retries} attempts")
            return False

    # ping check
    def ping(client, timeout=30):
        start_time = time.time() # Registra l'ora di inizio
        stdin, stdout, stderr = client.exec_command("ping -c 4 8.8.8.8")
        while not stdout.channel.exit_status_ready(): # Aspetta che il comando finisca
            if time.time() - start_time > timeout:
                client.exec_command("pkill -f 'ping -c 4 8.8.8.8'") # termina
                return "Ping timeout"
        output = stdout.read().decode('utf-8')
        if 'time=' in output:
            return "Ping succeeded"
        else: 
            return "Ping failed"

    # check bios or uefi mode
    def check_boot_mode():
        stdin, stdout, stderr = client.exec_command("cd /sys/firmware/efi")
        output = stdout.read().decode('utf-8')
        stderr = stderr.read().decode('utf-8')
        if stderr == '':
            print("Boot mode: UEFI")
        else:
            print("Boot mode: BIOS")

    # check disk size
    def check_resized_disk():
        url = f"{base_url}/qemu/{vmid}/config"
        response = metodo('get', url, headers)
        if response.status_code == 200:
            disk_info = response.json()['data']['scsi0']
            match = re.search(r'size=(\d+G)', disk_info)
            # Se non trovi la dimensione in G, cerca quella in M (MB)
            if not match:
                match = re.search(r'size=(\d+)(M)', disk_info) # se la dimensione in proxmox è in MB fa un altro check
                if match:
                    disk_size = round(float(match.group(1))/ 1024, 1) # Converti da MB a GB e arrotonda di un numero dopo la virgola
            else:
                disk_size = match.group(1)  # Dimensione in G
            stdin, stdout, stderr = client.exec_command("lsblk -o NAME,SIZE | grep sda | head -n 1")
            output = stdout.read().decode('utf-8')
            error = stderr.read().decode('utf-8')
            if str(disk_size) in output:
                print(f"Disk size matches with proxmox: {disk_size}")
            else:
                print(f"Disk size does not match with proxmox: {disk_size}, error: {error}")
        else:
            print(f"Disk size not found {disk_info}")

    # chech hostname
    def check_hostname():
        stdin, stdout, stderr = client.exec_command('getent hosts | awk /"${HOSTNAME:-${HOST-}}"./\'{print $2}\'')
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8')
        if hostname in output:
            print(f"Hostname matches with proxmox: {hostname}")
        else:
            print(f"Hostname does not match with proxmox: {hostname}, error: {error}")

    # chech fstrim
    def check_fstrim():
        stdin, stdout, stderr = client.exec_command("systemctl status fstrim.timer | grep \"Active:\" | awk '{print $2}'")
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8')
        if error == '':
            print(f"Fstrim status: {output}")
        else:
            print(f"Fstrim status error: {error}")

    # Check comando per aggiornamenti
    def check_comando_aggiornamenti(OS):
        OS = OS.strip()
        # Apri il file JSON in modalità lettura ('r')
        with open('main_project/os_list.json', 'r', encoding="utf-8") as file:
            OS_list = json.load(file)  # Carica il contenuto del file JSON in una variabile Python
        for item in OS_list:
            if any(OS in distro for distro in item['distro']): # controlla se OS è contenuto in una stringa della lista
                update_command = item['update_command'] # cerca qual'è il comando per fare l'aggiornamento
                return update_command
        print("OS non trovato!")  # Debug se non trova nulla
        return None  # Se non trova nulla, restituisce None

    # check OS
    def check_OS():
        stdin, stdout, stderr = client.exec_command("grep '^ID=' /etc/os-release | cut -d '=' -f2")
        output = stdout.read().decode('utf-8').replace('"', '').strip() # rimuove le virgolette di alcuni sistemi operativi
        error = stderr.read().decode('utf-8')
        update_command = check_comando_aggiornamenti(output)
        if update_command is None:
            return None
        return update_command

    # Configura il logger per gli errori
    error_logger = logging.getLogger('error_logger')
    error_handler = logging.FileHandler(os.path.join(log_dir, "error_log.txt"), mode="w") # logga sovrascrivendo cosa c'era prima
    error_handler.setLevel(logging.ERROR)
    error_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    error_handler.setFormatter(error_formatter)
    error_logger.addHandler(error_handler)

    # Configura il logger per gli aggiornamenti (successo)
    update_logger = logging.getLogger('update_logger')
    update_logger.setLevel(logging.DEBUG)
    update_handler = logging.FileHandler(os.path.join(log_dir, "update_log.txt"), mode="w") # logga sovrascrivendo cosa c'era prima
    update_handler.setLevel(logging.DEBUG)
    update_logger.propagate = False # Evita la propagazione dei log
    update_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    update_handler.setFormatter(update_formatter)
    update_logger.addHandler(update_handler)

    # aggiornamenti 
    def aggiornamento():
        update_command = check_OS()
        if update_command is None:
            print("Cannot perform update: OS not found")
            return # esci subito dalla funzione se l'OS non è trovato
        time.sleep(10)
        stdin, stdout, stderr = client.exec_command(update_command)
        output = stdout.read().decode('utf-8').strip()
        error = stderr.read().decode('utf-8').strip()
        update_logger.debug(output) # logga gli aggiornamenti
        if error: 
            error_logger.error(error) # logga gli errori
            print(f"Errors during update: see 'error_log.txt' for more info") # se presenti degli errori restituisce
        else:
            print(f"Update finished without errors!") # se presenti degli errori restituisce
        if output != '':
            print("To view updates logs see 'update_log.txt' for more info")

    # check cloud-init.target verificha che cloud-init abbia finito di inizializzare la Vm
    def check_cloud_init(timeout=300):
        output = ''
        print("Waiting for cloud-init to finish...")
        start_time = time.time()  # Registra l'ora di inizio
        while output != 'active': # ciclo che aspetta che cloud init finisca la configurazione per passare agli aggiornamenti
            stdin, stdout, stderr = client.exec_command("systemctl status cloud-init.target | grep \"Active:\" | awk '{print $2}'")
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8')
            if error:
                print(f"Error: {error}")
                break
            if time.time() - start_time > timeout:
                print("Cloud-init timeout after 5 minutes: try to manually update the VM")
                break
            time.sleep(5)
        if output == 'active':
            print("Cloud-init finished")
            aggiornamento()

    # shutdown VM
    def shutdownVM():
        url = f"{base_url}/qemu/{vmid}/status/current"
        response = metodo('get', url, headers)
        status = response.json()['data']['status'] # Filtro per ottenere solo lo status
        if status == 'stopped':
            print(f"VM {vmid} shutdown successfully")
            return True
        else:
            url = f"{base_url}/qemu/{vmid}/status/shutdown"
            response = metodo('post', url, headers, data={}) # proxmox si aspetta un json anche se vuoto
            shutdownVM()

    # stop VM
    def stopVM():
        url = f"{base_url}/qemu/{vmid}/status/current"
        response = metodo('get', url, headers)
        status = response.json()['data']['status'] # Filtro per ottenere solo lo status
        if status == 'stopped':
            print(f"VM {vmid} stopped successfully")
            return True
        else:
            url = f"{base_url}/qemu/{vmid}/status/stop"
            response = metodo('post', url, headers, data={}) # proxmox si aspetta un json anche se vuoto
            stopVM()

    # Delete VM
    def deleteVM():
        url = f"{base_url}/qemu/{vmid}/status/current"
        response = metodo('get', url, headers)
        status = response.json()['data']['status'] # Filtro per ottenere solo lo status
        if status == 'stopped':
            url = f"{base_url}/qemu/{vmid}"
            response = metodo('delete', url, headers)
            if response.status_code == 200:
                print(f"VM {vmid} deleted successfully")
            else:
                print(f"VM {vmid} delete failed: {describe_errors(response)}")
        else:
            url = f"{base_url}/qemu/{vmid}/status/stop"
            response = metodo('post', url, headers, data={}) # proxmox si aspetta un json anche se vuoto
            deleteVM()

    #--------------------INIZIO DELLO SCRIPT---------------------------#

    boot_counter = 0 # tiene conto di quale boot mode è stato provato
    i = 0
    while True:
        vmid = clone_vm(templateID) # definisce il primo vmid disponibile
        status = check_if_cloned(vmid)
        if status is True:
            print("-----------------------------\nSetting Proxmox configuration\n-----------------------------")
            resize_disk(vmid) # fa il resize del disco su proxmox
            set_hostname() # imposta l'hostname
            check_xterm_js() # fa il controllo se la porta seriale è presente sulla configurazione della macchina
            if boot_counter == 1:
                delete_efi_disk() # elimina il disco efi quando la vm viene avviata in bios
                i = 0 # reimposta la variabile a di cloud init a 0
            i, user = cloud_init(i) # imposta cloud init con dhcp/user
            boot_mode = set_boot_mode(boot_counter) # la prima volta setta la macchina in uefi mode 
            start_vm() # fa ripartire la VM
            boot_counter = get_IPvm(boot_counter)
            if boot_counter == 1:
                print("VM doesn't boot in UEFI mode")
                deleteVM()
                continue
            elif boot_counter == 2: # se è uguale a 1 vuol dire che non ha fatto il boot nè in UEFI nè in BIOS
                print("Unable to continue with tests; the VM doesn't boot in either UEFI or BIOS")
                stopVM()
                break
            else:
                print(f"Vm booted correctly in {boot_mode}")
                if boot_mode == 'UEFI': # solo se la macchina parte in uefi allora la elimina per fare la priva in bios
                    boot_counter = 1
                    deleteVM()
                    continue # torna al inizio del ciclo 

            print("------------------------------------\nChecking configuration inside the VM\n------------------------------------")
            ssh() # fa la prova di connessione ssh con la password di user, boot counter è un brutto nome per l'ip ma serve acnhe a controllare quante volte la macchian è stata fatta ripartire
            status = ssh_key() # test connessione ssh user con chiave privata
            if status is False:
                break
            print(f"DHCP: {ping(client)}") # risultato test config DHCP
            client.close() # chiute la connessione ssh
            client.get_host_keys().clear() # Rimuove tutte le chiavi host
            shutdownVM() # ferma la VM
            i, user = cloud_init(i, ip_addr) # cambia il cloud init con IPV4 ricevuto prima da dhcp \ i permette di cambiare 
            start_vm() # fa ripartire la VM
            boot_counter = get_IPvm(1) # al riavvio della macchina se non parte finisce il test
            if boot_counter == 2:
                print("Unable to continue with tests VM not Booted after reboot")
                stopVM()
                break
            else:
                ssh() # fa la prova di connessione ssh con la password di root
                status = ssh_key() # test connessione ssh root con chiave privata
                if status is False:
                    print("Unable to continue with tests cant connect with ssh")
                    break
                print(f"IPV4 Static: {ping(client)}") # risultato test config IPV4
                #check_boot_mode() # fa il check se la macchina è in bios o in uefi mode
                check_resized_disk() # verifica l'efettivo ridimensionamento del disco
                check_boot_mode() # verifica dentro la macchina il boot mode
                check_hostname() # comara l'hostname impostato su proxmox con quello efettivo nella macchina
                check_fstrim() # lancia il comando fstrim per liberare spazio
                check_cloud_init() # cerca prima se cloud-init ha finito di inizializzare la VM, poi cerca il sistema operativo, poi cerca di aggiornare i pacchetti
                client.close() # chiute la connessione ssh
                client.get_host_keys().clear() # Rimuove tutte le chiavi host
                stopVM()
            break
        else:
            break