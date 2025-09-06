\# Dominoz



Dominoz is a simple Python-based Dominoes game consisting of a \*\*server\*\* and a \*\*client\*\*. It allows multiple players to connect, create lobbies, chat, and play Dominoes in ASCII format (or CLI).



---



\## Features



\- Server-client architecture

\- Multiple lobbies supported

\- Create, join, and leave lobbies

\- Start games with 2–6 players per lobby

\- ASCII-based Dominoes gameplay

\- Chat with other players during your turn

\- Player stats and levels tracked



---



\## Installation



1\. Clone the repository:



```bash

git clone https://github.com/Simonko-912/Dominoz.git

cd Dominoz

````



2\. (Optional) Create a Python virtual environment:



```bash

python -m venv venv

source venv/bin/activate  # Linux/macOS

venv\\Scripts\\activate     # Windows

```



3\. Install dependencies (only standard library is needed):



```bash

\# No external libraries required

\# Only Python 3.x is needed

```



---



\## Usage



\### Server



```bash

python server.py

```



\* Follow the prompts to set server name, max players per lobby, max lobbies, and default difficulty.

\* The server listens on port `5555` by default.



\### Client



```bash

python client.py

```



\* Enter the server IP and port.

\* Choose a username.

\* Use commands to browse lobbies, create or join lobbies, play tiles, pass, chat, and quit.



---



\## Commands (Client)



\* `list` → List server and lobby info

\* `create` → Create a new lobby

\* `join <lobby\_id>` → Join an existing lobby

\* `leave` → Leave current lobby

\* `start` → Start the game (host only)

\* `status` → Get current lobby/game status

\* `move <a> <b> <side> \[chat]` → Play a tile

\* `pass \[chat]` → Pass your turn

\* `quit` → Quit the client



---



\## System Requirements



\* \*\*Minimum\*\*: Turns on (literally, the game will run on almost any device that runs python)

\* \*\*Recommended\*\*: Any modern PC, laptop, or even high-end smartphones



> No special hardware required. Just a device capable of running Python 3.x.



---



\## License



This project is licensed under the \*\*Apache 2.0\*\*.



---



\## Contributing



Feel free to fork the project, open issues, or submit pull requests.

Suggestions for new features, bug fixes, or optimizations are welcome.



---

