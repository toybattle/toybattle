import socket
def client():
   # Création d'un socket TCP
   client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   # Connexion au serveur
   server_ip = "127.0.0.1"
   server_port = 8000
   client_socket.connect((server_ip, server_port))
   try:
       while True:
           # Envoi d'un message au serveur
           message = input("Entrez un message : ")
           client_socket.send(message.encode("utf-8"))
           # Réception de la réponse du serveur
           response = client_socket.recv(1024).decode("utf-8")
           print(f"Réponse du serveur : {response}")
           # Arrêt si le serveur envoie "closed"
           if response.lower() == "closed":
               break
   finally:
       client_socket.close()
       print("Connexion fermée.")
client()