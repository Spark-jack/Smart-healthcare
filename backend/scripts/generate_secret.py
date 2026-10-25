import secrets

def generate_secret_key() -> str:
    key = secrets.token_urlsafe(48)
    return key

if __name__ == "__main__":
    key = generate_secret_key()
    print("=" * 60)
    print("Generated Secure JWT Secret Key (48 bytes / 64 URL-safe chars):")
    print(key)
    print("=" * 60)
    print("Add this to your backend/.env file:")
    print(f"SECRET_KEY={key}")
