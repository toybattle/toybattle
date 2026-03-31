import socket
def serveur():
   # Création d'un socket TCP
   server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   # Liaison à une adresse IP et un port
   server_ip = "127.0.0.1"
   server_port = 8000
   server_socket.bind((server_ip, server_port))
   # Écoute des connexions entrantes
   server_socket.listen(1)
   print(f"Serveur en écoute sur {server_ip}:{server_port}")
   client_socket, client_address = server_socket.accept()
   print(f"Connexion acceptée de {client_address}")
   try:
       while True:
           # Réception des données du client
           data = client_socket.recv(1024).decode("utf-8")
           if not data or data.lower() == "close":
               client_socket.send("closed".encode("utf-8"))
               break
           print(f"Message reçu : {data}")
           client_socket.send("Message reçu".encode("utf-8"))
   finally:
       client_socket.close()
       server_socket.close()
       print("Serveur arrêté.")
serveur()