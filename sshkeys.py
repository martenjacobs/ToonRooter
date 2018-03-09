def generate_key_pair(password=None):
    from cryptography.hazmat.backends import default_backend
    from cryptography.hazmat.primitives.asymmetric import rsa

    from cryptography.hazmat.primitives import serialization

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )

    key_encryption_algorithm = serialization.NoEncryption()
    if password:
        key_encryption_algorithm = serialization.BestAvailableEncryption(password)

    private_pem = private_key.private_bytes(
       encoding=serialization.Encoding.PEM,
       format=serialization.PrivateFormat.PKCS8,
       encryption_algorithm=key_encryption_algorithm
    )


    public_key = private_key.public_key()

    public_openssh = public_key.public_bytes(
       encoding=serialization.Encoding.OpenSSH,
       format=serialization.PublicFormat.OpenSSH
    )

    return (public_openssh, private_pem)

def check_public_key(data):
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.backends import default_backend
    try:
        key = serialization.load_ssh_public_key(
            data, default_backend())
        return True
    except:
        return False
