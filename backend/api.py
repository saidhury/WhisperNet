def handle_incoming_message(message: bytes, sender_ip: bytes):
    sender_ip_str = sender_ip.decode('utf-8', errors='ignore')
    message_str = message.decode('utf-8', errors='ignore')
    print(f"UDP message received from {sender_ip_str}: {message_str}")
