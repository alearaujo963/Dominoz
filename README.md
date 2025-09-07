<img width="1057" height="376" alt="Dominoz-small" src="https://github.com/user-attachments/assets/2389e413-81e5-4d77-aebb-a0f0d6cf2ffc" />
<p align="center"> 
    <img src="https://img.shields.io/github/issues/Simonko-912/Dominoz" alt="Issues">
    <img src="https://img.shields.io/github/forks/Simonko-912/Dominoz" alt="Forks">
    <img src="https://img.shields.io/github/stars/Simonko-912/Dominoz" alt="Stars">
    <img src="https://img.shields.io/badge/License-Apache%202.0-blue.svg" alt="License (Apache 2.0)">
    <img src="https://img.shields.io/badge/version-1.0.1-blue" alt="Version">
    <img src="https://img.shields.io/badge/contributors-0-orange" alt="Contributors">
    <img src="https://img.shields.io/github/downloads/Simonko-912/Dominoz/total" alt="Downloads">
    <img src="https://img.shields.io/badge/build-passing-brightgreen" alt="Build Status">
    <img src="https://img.shields.io/badge/Servers-Proposals%20Welcome-blue" alt="Server Proposals">
</p>


# Dominoz

Dominoz is a simple Python-based Dominoes game consisting of a **server** and a **client**. It allows multiple players to connect, create lobbies, chat, and play Dominoes in ASCII format (also called CLI).

---

## Features

- Server-client architecture
- Multiple lobbies supported
- Create, join, and leave lobbies
- Start games with 2–6 players per lobby
- ASCII-based Dominoes gameplay
- Chat with other players during your turn
- Player stats and levels tracked

---
## Server list
- Propose servers on issues

### Demo server:
- 147.185.221.31:48067
## Installation

1. Clone the repository:

```bash
git clone https://github.com/Simonko-912/Dominoz.git
cd Dominoz
````

2. (Optional) Create a Python virtual environment:

```bash
python -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows
```

3. Install dependencies (only standard library is needed):

```bash
# No external libraries required
# Only Python 3.x is needed
```

---

## Usage

### Server

```bash
python server.py
```

* Follow the prompts to set server name, max players per lobby, max lobbies, and default difficulty.
* The server listens on port `5555` by default.

### Client

```bash
python client.py
```

* Enter the server IP and port.
* Choose a username.
* Use commands to browse lobbies, create or join lobbies, play tiles, pass, chat, and quit.

---

## Commands (Client)

* `list` → List server and lobby info
* `create` → Create a new lobby
* `join <lobby_id>` → Join an existing lobby
* `leave` → Leave current lobby
* `start` → Start the game (host only)
* `status` → Get current lobby/game status
* `move <a> <b> <side> [chat]` → Play a tile
* `pass [chat]` → Pass your turn
* `quit` → Quit the client

---

## System Requirements

* **Minimum**: 
- CPU: Any 32 bit or 64 bit cpu that can run a os that python supports.
- RAM: Atleast ~16 mb of free ram.
- GPU: Your system's minimum. 
- Storage: Atleast ~50kb free for the python files and atleast ~7mb for the .exe
- Python 3.8.*

* **Recommended**:
- CPU: I5 6th gen
- RAM: 4 gb ram
- GPU: Intel HD graphics
- Storage: 100mb recomended
- Latest python

---

## License

This project is dual-licensed under **Apache 2.0** and **GPLv3**. You can choose either license for your use.

---

## Contributing

Feel free to fork the project, open issues, or submit pull requests.
Suggestions for new features, bug fixes, or optimizations are welcome.

---
