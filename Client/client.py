"""
Dominoes Client (prototype)
- Connects to the server and allows lobby browsing, creating, joining, starting (if host)
- Plays with ASCII dominos, chooses left/right placement, sends chat per move
"""

import socket
import pickle
import threading
import time

def print_logo():
    logo = r"""
                                                                                                                                                    
                                                                                                                                                    
                                                                           %@@@@@@@@&                                                               
                                                                     @@@@@@@@@@@@@@@@@@@@@@                                                         
                                                                  @@@@@@@              &@@@@@@#                                                     
                                                                @@@@@    #@@@@@@@@@@@@@    @@@@@%                                                   
                                                                      @@@@@@@@#,.#@@@@@@@@*                                                         
                                                                    @@@@@     *@@/     #@@@@                                                        
                                                                         .@@@@@@@@@@@@%                                                             
                                                                         @@@@      &@@@,                                                            
        ,.....                                                               .@@@@@                                                                 
     %@@@@@@@@@@@@@@@@                                                       &@@@@@                                                                 
     %@@@@@@@@@@@@@@@@@@.                                                                                                                           
     %@@@@@        @@@@@@@       ,@@@@@@@&        @@@@  #@@@@     &@@@@       @@@@(   ,@@@@  ,@@@@%            @@@@@@@@        @@@@@@@@@@@@@@&      
     %@@@@@         (@@@@@@   #@@@@@@@@@@@@@@    @@@@@@@@@@@@@@@@@@@@@@@@@   &@@@@@   @@@@@@@@@@@@@@@@      @@@@@@@@@@@@@@    @@@@@@@@@@@@@@@@@     
     %@@@@@          @@@@@@  @@@@@@@% /@@@@@@@   @@@@@@@@@@@@@@@@@@@@@@@@@/  &@@@@@   @@@@@@@@@@@@@@@@@   @@@@@@@@..@@@@@@@&   %@@@@@@@@@@@@@.      
     %@@@@@         @@@@@@* (@@@@@       @@@@@@  @@@@@@    @@@@@@    @@@@@@  &@@@@@   @@@@@@      @@@@@(  @@@@@@      @@@@@@       @@@@@@@&         
     %@@@@@       @@@@@@@%   @@@@@@     %@@@@@@  @@@@@@    @@@@@@    @@@@@@  &@@@@@   @@@@@@      @@@@@(  @@@@@@      @@@@@@    #@@@@@@@            
     %@@@@@@@@@@@@@@@@@@     .@@@@@@@@@@@@@@@@   @@@@@@    @@@@@@    @@@@@@  &@@@@@   @@@@@@      @@@@@(   @@@@@@@@@@@@@@@@   @@@@@@@@@@@@@@@@@     
     #@@@@@@@@@@@@@@@          .@@@@@@@@@@@@     @@@@@@    @@@@@@    @@@@@@  &@@@@@   @@@@@@      @@@@@(     @@@@@@@@@@@@    /@@@@@@@@@@@@@@@@@     
                                                                                                                                               
     Client app    
    """
    print(logo)
print_logo()

def print_chain(chain):
    if not chain:
        return "<empty>"
    return " ".join(f"[{a}|{b}]" for a,b in chain)

def print_hand(hand):
    return " ".join(f"[{a}|{b}]" for a,b in hand)

def recv_loop(sock):
    # background receiver prints messages and updates shared state by calling callbacks
    while True:
        try:
            data = sock.recv(4096)
            if not data:
                print("Connection closed by server.")
                break
            msg = pickle.loads(data)
            handle_server_message(msg)
        except Exception as e:
            #print("recv error:", e)
            break

# global client state (kept simple)
CURRENT_LOBBY = None
YOUR_HAND = []
PLAYERS_IN_LOBBY = []
CURRENT_TURN = None
USERNAME = None

def handle_server_message(msg):
    global CURRENT_LOBBY, YOUR_HAND, PLAYERS_IN_LOBBY, CURRENT_TURN
    if "server_info" in msg:
        si = msg["server_info"]
        print("=== Server Info ===")
        print(f"Server: {si['server_name']} | Lobbies: {si['current_lobby_count']} / {si['max_lobbies']} | Players connected: {si['players_connected']}")
        for l in si["lobbies"]:
            print(f" Lobby {l['lobby_id']}: host={l['host']} players={l['players']}/{l['max_players']} diff={l['difficulty']} started={l['started']}")
    if "joined" in msg:
        CURRENT_LOBBY = msg.get("lobby_id")
        PLAYERS_IN_LOBBY = msg.get("players",[])
        print(f"Joined lobby {CURRENT_LOBBY}. Players: {PLAYERS_IN_LOBBY} | difficulty: {msg.get('difficulty')}")
    if "lobby_update" in msg:
        info = msg["lobby_update"]
        print("Lobby update:", info)
        if "players" in info:
            PLAYERS_IN_LOBBY[:] = info["players"]
            print("Players now:", PLAYERS_IN_LOBBY)
    if "created" in msg:
        print("Created lobby id", msg["lobby_id"])
    if "game_start" in msg:
        CURRENT_LOBBY = msg.get("lobby_id")
        YOUR_HAND = msg.get("your_hand", [])
        PLAYERS_IN_LOBBY = msg.get("players", [])
        CURRENT_TURN = msg.get("turn")
        print("=== Game started ===")
        print("Players:", PLAYERS_IN_LOBBY)
        print("Your hand:", print_hand(YOUR_HAND))
        print("Chain:", print_chain(msg.get("chain", [])))
        print("Current turn:", CURRENT_TURN)
    if "chat" in msg:
        print("[chat]", msg["chat"])
    if "update" in msg:
        u = msg["update"]
        CURRENT_TURN = u.get("turn")
        print("=== Update ===")
        if "placed_by" in u:
            print(f"{u['placed_by']} placed {print_chain([u['placed_tile']])}")
        print("Chain:", print_chain(u.get("chain", [])))
        print("Hands sizes:", u.get("hands_sizes"))
        print("Turn:", CURRENT_TURN)
        # request status to update our hand if we are in a lobby
    if "error" in msg:
        print("[server error]", msg["error"])
    if "status" in msg:
        st = msg["status"]
        YOUR_HAND = st.get("your_hand", YOUR_HAND)
        PLAYERS_IN_LOBBY = st.get("players", PLAYERS_IN_LOBBY)
        CURRENT_TURN = st.get("turn", CURRENT_TURN)
        print("=== Lobby status ===")
        print("Players:", PLAYERS_IN_LOBBY)
        print("Your hand:", print_hand(YOUR_HAND))
        print("Chain:", print_chain(st.get("chain", [])))
        print("Turn:", CURRENT_TURN)
        print("Your level:", st.get("your_level"))
    if "game_over" in msg:
        go = msg["game_over"]
        if go.get("blocked"):
            print("Game blocked! Winner (least pips):", go["winner"])
            print("Pip sums:", go["sums"])
        else:
            print("Game over! Winner:", go["winner"])
        print("Final hands:", {u: print_hand(h) for u,h in go.get("hands",{}).items()})

# --- Client UI / commands ---

def main():
    global USERNAME, CURRENT_LOBBY, YOUR_HAND
    server_ip = input("Server IP (default 127.0.0.1): ").strip() or "127.0.0.1"
    server_port = int(input("Server port (default 5555): ").strip() or 5555)
    USERNAME = input("Choose your username: ").strip() or f"guest_{int(time.time())%1000}"

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect((server_ip, server_port))

    # say hello
    sock.send(pickle.dumps({"action":"hello", "username": USERNAME}))
    # start receiver thread
    t = threading.Thread(target=recv_loop, args=(sock,), daemon=True)
    t.start()

    # main command loop
    help_text = """
Commands:
 list                        -> list server & lobbies
 create                      -> create a lobby
 join <lobby_id>             -> join an existing lobby
 leave                       -> leave current lobby
 start                       -> start the game (host only)
 status                      -> get current lobby/game status
 move <a> <b> <side> [chat]  -> play tile (side = left|right). include optional chat in quotes
 pass [chat]                 -> pass your turn and optionally send chat
 quit                        -> quit
"""
    print(help_text)
    try:
        while True:
            cmd = input("> ").strip()
            if not cmd:
                continue
            parts = cmd.split()
            if parts[0] == "list":
                sock.send(pickle.dumps({"action":"list"}))
            elif parts[0] == "create":
                mp = input(f"Max players for this lobby (default {4}): ").strip()
                difficulty = input("Lobby difficulty (easy/normal/hard) (enter to use server default): ").strip()
                payload = {"action":"create_lobby"}
                if mp:
                    try: payload["max_players"] = int(mp)
                    except: pass
                if difficulty:
                    payload["difficulty"] = difficulty
                sock.send(pickle.dumps(payload))
            elif parts[0] == "join":
                if len(parts) < 2:
                    print("Usage: join <lobby_id>")
                    continue
                lid = int(parts[1])
                sock.send(pickle.dumps({"action":"join_lobby", "lobby_id": lid}))
                CURRENT_LOBBY = lid
            elif parts[0] == "leave":
                if not CURRENT_LOBBY:
                    print("Not in a lobby.")
                    continue
                sock.send(pickle.dumps({"action":"leave_lobby", "lobby_id": CURRENT_LOBBY}))
                CURRENT_LOBBY = None
            elif parts[0] == "start":
                if not CURRENT_LOBBY:
                    print("Not in a lobby.")
                    continue
                sock.send(pickle.dumps({"action":"start_lobby", "lobby_id": CURRENT_LOBBY}))
            elif parts[0] == "status":
                if not CURRENT_LOBBY:
                    print("Not in a lobby.")
                    continue
                sock.send(pickle.dumps({"action":"status", "lobby_id": CURRENT_LOBBY}))
            elif parts[0] == "move":
                if not CURRENT_LOBBY:
                    print("Join a lobby first.")
                    continue
                if len(parts) < 4:
                    print("Usage: move <a> <b> <side> [chat]")
                    continue
                try:
                    a = int(parts[1]); b = int(parts[2])
                except:
                    print("tile numbers must be ints 0..6")
                    continue
                side = parts[3] if parts[3] in ("left","right") else "right"
                chat = " ".join(parts[4:]) if len(parts) > 4 else ""
                sock.send(pickle.dumps({"action":"move", "lobby_id": CURRENT_LOBBY, "move": (a,b), "side": side, "chat": chat}))
            elif parts[0] == "pass":
                if not CURRENT_LOBBY:
                    print("Join a lobby first.")
                    continue
                chat = " ".join(parts[1:]) if len(parts) > 1 else ""
                sock.send(pickle.dumps({"action":"move", "lobby_id": CURRENT_LOBBY, "move": "pass", "chat": chat}))
            elif parts[0] == "quit":
                print("Bye")
                break
            else:
                print("Unknown command.")
                print(help_text)
    except KeyboardInterrupt:
        pass
    finally:
        sock.close()

if __name__ == "__main__":
    main()
