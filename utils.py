import os
from OpenSSL import crypto
import socket

def generate_self_signed_cert():
    """
    Generates a self-signed SSL certificate and key if they don't exist.
    """
    cert_path = "cert.pem"
    key_path = "key.pem"
    if not os.path.exists(cert_path) or not os.path.exists(key_path):
        print("🔐 Generating self-signed SSL certificate...")
        # Create a key pair
        k = crypto.PKey()
        k.generate_key(crypto.TYPE_RSA, 4096)

        # Create a self-signed certificate
        cert = crypto.X509()
        cert.get_subject().C = "IN"
        cert.get_subject().ST = "Maharashtra"
        cert.get_subject().L = "Pune"
        cert.get_subject().O = "YOLOv10 Project"
        cert.get_subject().OU = "Development"
        cert.get_subject().CN = "localhost"
        cert.set_serial_number(1000)
        cert.gmtime_adj_notBefore(0)
        cert.gmtime_adj_notAfter(10*365*24*60*60)  # Valid for 10 years
        cert.set_issuer(cert.get_subject())
        cert.set_pubkey(k)
        cert.sign(k, 'sha512')

        with open(cert_path, "wt") as f:
            f.write(crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode("utf-8"))
        with open(key_path, "wt") as f:
            f.write(crypto.dump_privatekey(crypto.FILETYPE_PEM, k).decode("utf-8"))
        print(f"✅ Certificate '{cert_path}' and key '{key_path}' created.")

    return cert_path, key_path

def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(('10.255.255.255', 1))
    IP = s.getsockname()[0]
    s.close()
    return IP