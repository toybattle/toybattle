# Présentation du module `socket` en Python

## 1. Introduction

Le module `socket` de Python (bibliothèque standard) permet de programmer des communications réseau bas niveau (TCP, UDP, AF_INET, AF_INET6, AF_UNIX, etc.).

Objectif : créer, envoyer, recevoir des données entre deux programmes par réseau.

## 2. Concepts clés

- `socket.socket(family, type, proto=0)` : crée un objet socket.
- Familles : `AF_INET` (IPv4), `AF_INET6` (IPv6), `AF_UNIX` (socket local UNIX).
- Types : `SOCK_STREAM` (TCP), `SOCK_DGRAM` (UDP), `SOCK_RAW` (brut).
- Méthodes courantes : `bind`, `listen`, `accept`, `connect`, `send`, `recv`, `sendto`, `recvfrom`, `close`.

## 3. Serveur TCP (exemple)

```python
import socket

HOST = '127.0.0.1'
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    print('Serveur en écoute sur', (HOST, PORT))
    conn, addr = s.accept()
    with conn:
        print('Connexion établie par', addr)
        while True:
            data = conn.recv(1024)
            if not data:
                break
            print('Reçu :', data)
            conn.sendall(data)
```

## 4. Client TCP (exemple)

```python
import socket

HOST = '127.0.0.1'
PORT = 65432

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.connect((HOST, PORT))
    s.sendall(b'Bonjour serveur')
    data = s.recv(1024)

print('Reçu du serveur', repr(data))
```

## 5. Serveur/Client UDP (concept)

- Le serveur utilise `s.bind((host, port))`, `s.recvfrom(bufsize)`, `s.sendto(data, addr)`.
- Le client utilise `s.sendto(data, (host, port))`, `s.recvfrom(bufsize)`.

## 6. Fonctions utilitaires

- `socket.gethostname()` : nom de la machine.
- `socket.gethostbyname(hostname)` : résolution DNS.
- `socket.getaddrinfo(host, port, family=0, type=0, proto=0, flags=0)` : info d'adresse.
- `socket.setdefaulttimeout(timeout)` : délai d’attente global.

## 7. Codeurs/décodeurs

- `socket.inet_aton` / `socket.inet_ntoa` pour conversions IPv4.
- `socket.inet_pton` / `socket.inet_ntop` pour IPv4/IPv6.

## 8. Points de vigilance

- Socket bloquantes vs non-bloquantes : `s.setblocking(False)`.
- Gestion des erreurs avec `socket.error` (ou `OSError`).
- Fermeture propre : `finally: s.close()` ou `with socket.socket(...) as s:`.
- Sécurité : validation, chiffrement (ssl.wrap_socket, module `ssl`).

## 9. Bonnes pratiques

- Ne jamais envoyer de données sensibles en clair sans TLS/SSL.
- Limiter le buffer de réception et gérer les fragments.
- Utiliser `selectors` ou `asyncio` pour sockets multiples/IO non bloquante.
- Tester en local et sur différentes configurations réseau.

## 10. Ressources complémentaires

- Documentation officielle Python : https://docs.python.org/3/library/socket.html
- Exemples et tutoriels : réseaux, jeux, HTTP persistant.
