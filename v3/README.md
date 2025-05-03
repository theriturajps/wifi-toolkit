This enhanced script creates a fake Wi-Fi network with a captive portal that mimics a login page. When users connect, they're redirected to a fake login page. Submitted credentials are captured and displayed in real-time.

# Key Features
- Fake Wi-Fi Network Creation
- Automatic Captive Portal (HTML login page)
- Real-time Credential Capture (Terminal + creds.txt)
- Success Page After Login
- MAC Spoofing & Deauth Attack Options

# How It Works
1. Creates Fake Wi-Fi with specified SSID (open or password-protected)
2. Launches Captive Portal (HTTP server on port 8080)
3. Redirects Users to a fake login page when they connect
4. Captures Credentials and displays them in real-time
5. Shows Success Page after "login" to avoid suspicion
6. Saves Credentials to creds.txt
