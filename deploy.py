#!/usr/bin/env python3

import os
import secrets
from getpass import getpass

# Upgrade Packages
os.system('sudo apt -y update')
os.system('sudo apt -y upgrade')

# Install NGINX
os.system('sudo apt install -y nginx')

# Enable Firewall
os.system('sudo ufw allow \'Nginx Full\'')
os.system('sudo ufw allow OpenSSH')
os.system('echo \'y\' | sudo ufw enable')

# Install APT Dependencies
os.system('sudo apt install -y '
          'python3-pip python3-dev build-essential libssl-dev libffi-dev python3-setuptools python3-venv')

# Create Virtual Env and Install PIP Dependencies
os.system('python3 -m venv venv')
REAL_PATH = os.environ['PATH']
os.environ['PATH'] = f'venv/bin:{REAL_PATH}'  # Temporarily override PATH, since we aren't activating the virtual env
os.system('venv/bin/pip install wheel')
os.system('venv/bin/pip install -r requirements.txt')
os.environ['PATH'] = REAL_PATH  # Restore the PATH variable to its original value

# Configure Application
os.system('rm .env')
secret_key = secrets.token_hex(32)
os.system(f'echo \'SECRET_KEY={secret_key}\' > .env')
while True:
    admin_password = getpass('Admin Password: ')
    confirm_password = getpass('Confirm: ')
    if not admin_password:
        print('Please enter a password.')
        continue
    if admin_password != confirm_password:
        print('Passwords do not match!')
        continue
    break
os.system(f'echo \'USERS={{"admin":"{admin_password}"}}\' >> .env')

# Write SystemD Service Unit
service_file = '/etc/systemd/system/login_app.service'
os.system(f'sudo touch {service_file}')
os.system(f'echo \'[Unit]\' | sudo tee -a {service_file}')
os.system(f'echo \'Description=Gunicorn instance to serve login app\' | sudo tee -a {service_file}')
os.system(f'echo \'After=network.target\' | sudo tee -a {service_file}')
os.system(f'echo \'\' | sudo tee -a {service_file}')
os.system(f'echo \'[Service]\' | sudo tee -a {service_file}')
os.system(f'echo \'User={os.getlogin()}\' | sudo tee -a {service_file}')
os.system(f'echo \'Group=www-data\' | sudo tee -a {service_file}')
os.system(f'echo \'WorkingDirectory={os.getcwd()}\' | sudo tee -a {service_file}')
os.system(f'echo \'Environment="PATH={os.path.join(os.getcwd(), "venv/bin")}"\' | sudo tee -a {service_file}')
os.system(f'echo \'ExecStart={os.path.join(os.getcwd(), "venv/bin/gunicorn")} '
          f'--workers 3 --bind unix:login_app.sock -m 007 wsgi:app\' | sudo tee -a {service_file}')
os.system(f'echo \'\' | sudo tee -a {service_file}')
os.system(f'echo \'[Install]\' | sudo tee -a {service_file}')
os.system(f'echo \'WantedBy=multi-user.target\' | sudo tee -a {service_file}')

# Enable SystemD System Unit
os.system('sudo systemctl enable login_app')
os.system('sudo systemctl start login_app')

# Get Domain Name
domain_name = input('Domain Name [Leave blank for no domain name]: ').strip()

# Configure NGINX
os.system('sudo unlink /etc/nginx/sites-enabled/*')
nginx_file = '/etc/nginx/sites-available/login'
os.system(f'sudo touch {nginx_file}')
os.system(f'echo \'server {{\' | sudo tee -a {nginx_file}')
os.system(f'echo \'    listen 80;\' | sudo tee -a {nginx_file}')
os.system(f'echo \'    server_name {domain_name or "_"};\' | sudo tee -a {nginx_file}')
os.system(f'echo \'    \' | sudo tee -a {nginx_file}')
os.system(f'echo \'    location / {{\' | sudo tee -a {nginx_file}')
os.system(f'echo \'        include proxy_params;\' | sudo tee -a {nginx_file}')
os.system(f'echo \'        proxy_pass http://unix:{os.path.join(os.getcwd(), "login_app.sock")};\' '
          f'| sudo tee -a {nginx_file}')
os.system(f'echo \'    }}\' | sudo tee -a {nginx_file}')
os.system(f'echo \'}}\' | sudo tee -a {nginx_file}')
os.system(f'sudo ln -s {nginx_file} /etc/nginx/sites-enabled')
os.system('sudo systemctl restart nginx')

# Configure TLS with Let's Encrypt (Only if domain name was provided)
if domain_name:
    configure_tls = None
    options = ['y', 'yes', 'n', 'no']
    while configure_tls not in options:
        configure_tls = input('Automatically configure TLS with Let\'s Encrypt? (y/n): ').strip().lower()
    if configure_tls in options[:2]:
        os.system('sudo apt install -y python3-certbot-nginx')
        os.system(f'sudo certbot --non-interactive --agree-tos --register-unsafely-without-email --nginx --redirect '
                  f'-d {domain_name}')
        os.system('sudo systemctl restart nginx')
