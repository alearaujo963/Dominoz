"""
Dominoes Server (prototype)
- supports multiple lobbies
- server settings provided at startup (server name, max players per lobby, max lobbies, difficulty)
- in-memory player stats and levels
- clients talk via pickle-serialized dicts
"""

import socket
import threading
import pickle
import random
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
                                                                                                                                               
     Server app    
    """
    print(logo)
print_logo()

# --- Helper functions and classes ---

def make_domino_set(max_pip=6):
    return [(i, j) for i in range(max_pip + 1) for j in range(i, max_pip + 1)]

def sum_pips(hand):
    return sum(a + b for a, b in hand)

def player_level(wins, games):
    if games == 0: return 0
    ratio = wins / games
    return int(ratio * 10)  # scale 0..10

def orient_for_left(tile, left_val):
    a, b = tile
    if b == left_val:
        return (a, b)  # new_tile right == left_val
    if a == left_val:
        return (b, a)
    return None

def orient_for_right(tile, right_val):
    a, b = tile
    if a == right_val:
        return (a, b)  # new_tile left == right_val
    if b == right_val:
        return (b, a)
    return None

# --- Server state ---

class Lobby:
    def __init__(self, lobby_id, max_players, difficulty, host_name):
        self.lobby_id = lobby_id
        self.max_players = max_players
        self.difficulty = difficulty  # "easy"/"normal"/"hard"
        self.host_name = host_name
        self.players = []  # list of (conn, username, stats_ref)
        self.player_names = []
        self.started = False
        self.chain = []
        self.hands = {}  # username -> list of tiles
        self.turn_index = 0
        self.passes_in_row = 0
        self.lock = threading.Lock()

    def current_turn_username(self):
        if not self.players: return None
        return self.player_names[self.turn_index % len(self.player_names)]

    def broadcast(self, payload):
        # sends payload to all clients in this lobby (non-blocking best-effort)
        for conn, uname, stats in list(self.players):
            try:
                conn.send(pickle.dumps(payload))
            except:
                pass

class GameServer:
    def __init__(self, host, port, server_name, max_players_per_lobby, max_lobbies, difficulty):
        self.host = host
        self.port = port
        self.server_name = server_name
        self.max_players_per_lobby = max_players_per_lobby
        self.max_lobbies = max_lobbies
        self.default_difficulty = difficulty.lower()
        self.lobbies = {}  # lobby_id -> Lobby
        self.next_lobby_id = 1
        self.clients = {}  # conn -> (username, stats)
        self.stats = {}    # username -> {"wins":int,"games":int}
        self.lock = threading.Lock()
        self.sock = None
        self.running = True

    def create_lobby(self, host_name, requested_max=None, difficulty=None):
        with self.lock:
            if len(self.lobbies) >= self.max_lobbies:
                return None, "No lobby slots available on server."
            lid = self.next_lobby_id
            self.next_lobby_id += 1
            mp = requested_max if requested_max else self.max_players_per_lobby
            diff = difficulty if difficulty else self.default_difficulty
            lobby = Lobby(lid, mp, diff, host_name)
            self.lobbies[lid] = lobby
            return lobby, None

    def remove_lobby_if_empty(self, lid):
        with self.lock:
            lobby = self.lobbies.get(lid)
            if not lobby:
                return
            if not lobby.players:
                del self.lobbies[lid]

    def list_servers_info(self):
        # return basic server info
        with self.lock:
            info = {
                "server_name": self.server_name,
                "max_lobbies": self.max_lobbies,
                "max_players_per_lobby": self.max_players_per_lobby,
                "default_difficulty": self.default_difficulty,
                "current_lobby_count": len(self.lobbies),
                "players_connected": len(self.clients),
            }
            # per-lobby short info
            info["lobbies"] = []
            for lid, l in self.lobbies.items():
                info["lobbies"].append({
                    "lobby_id": lid,
                    "host": l.host_name,
                    "players": len(l.players),
                    "max_players": l.max_players,
                    "difficulty": l.difficulty,
                    "started": l.started
                })
            return info

    def client_thread(self, conn, addr):
        try:
            # initial handshake: expect {"action":"hello","username":str}
            data = pickle.loads(conn.recv(4096))
            if not isinstance(data, dict) or data.get("action") != "hello":
                conn.send(pickle.dumps({"error":"Invalid hello"}))
                conn.close()
                return
            username = data.get("username", f"guest_{addr[1]}")
            with self.lock:
                # register client
                self.clients[conn] = (username, self.stats.setdefault(username, {"wins":0,"games":0}))
            conn.send(pickle.dumps({"ok": True, "server_info": self.list_servers_info()}))

            # listen for client requests
            while self.running:
                try:
                    raw = conn.recv(4096)
                    if not raw:
                        break
                    req = pickle.loads(raw)
                except Exception:
                    break

                if not isinstance(req, dict):
                    continue

                action = req.get("action")

                # --- list server info ---
                if action == "list":
                    conn.send(pickle.dumps({"server_info": self.list_servers_info()}))

                # --- create lobby ---
                elif action == "create_lobby":
                    requested_max = req.get("max_players")
                    difficulty = req.get("difficulty")
                    lobby, err = self.create_lobby(username, requested_max, difficulty)
                    if lobby is None:
                        conn.send(pickle.dumps({"error": err}))
                    else:
                        conn.send(pickle.dumps({"created": True, "lobby_id": lobby.lobby_id}))
                
                # --- join lobby ---
                elif action == "join_lobby":
                    lid = req.get("lobby_id")
                    lobby = self.lobbies.get(lid)
                    if not lobby:
                        conn.send(pickle.dumps({"error":"Lobby not found"}))
                        continue
                    with lobby.lock:
                        if len(lobby.players) >= lobby.max_players:
                            conn.send(pickle.dumps({"error":"Lobby full"}))
                            continue
                        # add player
                        with self.lock:
                            stats_ref = self.stats.setdefault(username, {"wins":0,"games":0})
                        lobby.players.append((conn, username, stats_ref))
                        lobby.player_names.append(username)
                        conn.send(pickle.dumps({"joined": True, "lobby_id": lid, "players": lobby.player_names, "difficulty": lobby.difficulty, "max_players": lobby.max_players}))
                        # notify others in lobby
                        lobby.broadcast({"lobby_update": {"players": lobby.player_names}})
                
                # --- leave lobby ---
                elif action == "leave_lobby":
                    lid = req.get("lobby_id")
                    lobby = self.lobbies.get(lid)
                    if not lobby:
                        conn.send(pickle.dumps({"error":"Lobby not found"}))
                        continue
                    with lobby.lock:
                        # remove player
                        removed = False
                        for i, (c, uname, stats) in enumerate(list(lobby.players)):
                            if c == conn:
                                lobby.players.pop(i)
                                lobby.player_names.pop(i)
                                removed = True
                                break
                        if removed:
                            lobby.broadcast({"lobby_update":{"players": lobby.player_names}})
                            conn.send(pickle.dumps({"left":True}))
                    self.remove_lobby_if_empty(lid)

                # --- start game (host only) ---
                elif action == "start_lobby":
                    lid = req.get("lobby_id")
                    lobby = self.lobbies.get(lid)
                    if not lobby:
                        conn.send(pickle.dumps({"error":"Lobby not found"})); continue
                    if username != lobby.host_name:
                        conn.send(pickle.dumps({"error":"Only host can start"})); continue
                    with lobby.lock:
                        if lobby.started:
                            conn.send(pickle.dumps({"error":"Already started"})); continue
                        if len(lobby.players) < 2:
                            conn.send(pickle.dumps({"error":"Need at least 2 players to start"})); continue
                        # start a game
                        lobby.started = True
                        # prepare domino deck and deal based on difficulty
                        deck = make_domino_set(6)
                        random.shuffle(deck)
                        per_player = 8 if lobby.difficulty == "easy" else 12 if lobby.difficulty == "normal" else 14
                        hands = {}
                        for _, uname, _ in lobby.players:
                            hand = [deck.pop() for _ in range(min(per_player, len(deck)))]
                            hands[uname] = hand
                        lobby.chain = []
                        lobby.hands = hands
                        lobby.turn_index = 0
                        lobby.passes_in_row = 0
                        # flag each player's 'started' status by sending initial update
                        for conn2, uname2, _ in lobby.players:
                            try:
                                conn2.send(pickle.dumps({"game_start": True, "lobby_id": lid, "your_hand": hands[uname2], "players": lobby.player_names, "turn": lobby.current_turn_username(), "chain": lobby.chain}))
                            except:
                                pass

                # --- move (place tile or pass). payload: {"action":"move", "lobby_id":int, "move": (a,b) or "pass", "side":"left"|"right", "chat": str} ---
                elif action == "move":
                    lid = req.get("lobby_id")
                    lobby = self.lobbies.get(lid)
                    if not lobby:
                        conn.send(pickle.dumps({"error":"Lobby not found"})); continue
                    with lobby.lock:
                        # determine who this is
                        player_index = None
                        for idx, (c, uname, _) in enumerate(lobby.players):
                            if c == conn:
                                player_index = idx
                                break
                        if player_index is None:
                            conn.send(pickle.dumps({"error":"You are not in the lobby"})); continue
                        if lobby.player_names[lobby.turn_index % len(lobby.player_names)] != username:
                            conn.send(pickle.dumps({"error":"Not your turn"})); continue

                        move = req.get("move")
                        chat = req.get("chat","")
                        side = req.get("side","right")
                        # broadcast chat first if present
                        if chat:
                            lobby.broadcast({"chat": f"{username}: {chat}"})

                        if move == "pass":
                            lobby.passes_in_row += 1
                            lobby.turn_index = (lobby.turn_index + 1) % len(lobby.player_names)
                            lobby.broadcast({"update": {"chain": lobby.chain, "hands_sizes": {u: len(h) for u,h in lobby.hands.items()}, "turn": lobby.current_turn_username()}})
                        else:
                            # attempt to place tile
                            tile = tuple(move)
                            hand = lobby.hands.get(username, [])
                            if tile not in hand and (tile[1], tile[0]) not in hand:
                                conn.send(pickle.dumps({"error":"You don't have that tile", "your_hand": hand}))
                                continue
                            if not lobby.chain:
                                # place as is
                                # orient tile so it appears [a|b] and will be the only tile
                                if tile in hand:
                                    placed = tile
                                    hand.remove(tile)
                                else:
                                    placed = (tile[1], tile[0])
                                    hand.remove((tile[1], tile[0]))
                                lobby.chain.append(placed)
                                lobby.passes_in_row = 0
                                lobby.turn_index = (lobby.turn_index + 1) % len(lobby.player_names)
                                lobby.broadcast({"update": {"placed_by":username, "placed_tile": placed, "chain": lobby.chain, "hands_sizes": {u: len(h) for u,h in lobby.hands.items()}, "turn": lobby.current_turn_username()}})
                            else:
                                if side not in ("left","right"): side = "right"
                                if side == "left":
                                    left_val = lobby.chain[0][0]  # leftmost face
                                    oriented = orient_for_left(tile, left_val)
                                    if oriented is None:
                                        conn.send(pickle.dumps({"error":"Tile does not match left end", "your_hand": hand}))
                                        continue
                                    # remove tile (in whatever orientation it's in)
                                    if tile in hand:
                                        hand.remove(tile)
                                    else:
                                        hand.remove((tile[1], tile[0]))
                                    lobby.chain.insert(0, oriented)
                                    lobby.passes_in_row = 0
                                    lobby.turn_index = (lobby.turn_index + 1) % len(lobby.player_names)
                                    lobby.broadcast({"update": {"placed_by":username, "placed_tile": oriented, "chain": lobby.chain, "hands_sizes": {u: len(h) for u,h in lobby.hands.items()}, "turn": lobby.current_turn_username()}})
                                else:
                                    right_val = lobby.chain[-1][1]
                                    oriented = orient_for_right(tile, right_val)
                                    if oriented is None:
                                        conn.send(pickle.dumps({"error":"Tile does not match right end", "your_hand": hand}))
                                        continue
                                    if tile in hand:
                                        hand.remove(tile)
                                    else:
                                        hand.remove((tile[1], tile[0]))
                                    lobby.chain.append(oriented)
                                    lobby.passes_in_row = 0
                                    lobby.turn_index = (lobby.turn_index + 1) % len(lobby.player_names)
                                    lobby.broadcast({"update": {"placed_by":username, "placed_tile": oriented, "chain": lobby.chain, "hands_sizes": {u: len(h) for u,h in lobby.hands.items()}, "turn": lobby.current_turn_username()}})
                        # check win condition (someone has 0 tiles)
                        winner = None
                        for u,h in lobby.hands.items():
                            if len(h) == 0:
                                winner = u
                                break
                        if winner:
                            # update stats
                            with self.lock:
                                self.stats[winner]["wins"] += 1
                                for u in lobby.hands:
                                    self.stats[u]["games"] += 1
                            lobby.broadcast({"game_over": {"winner": winner, "hands": lobby.hands}})
                            # reset lobby state to allow restart later
                            lobby.started = False
                            lobby.hands = {}
                            lobby.chain = []
                            lobby.turn_index = 0
                            continue
                        # check blocked condition: if passes_in_row >= number players -> blocked
                        if lobby.passes_in_row >= len(lobby.player_names) and lobby.passes_in_row > 0:
                            # compute least pip sum
                            sums = {u: sum_pips(h) for u,h in lobby.hands.items()}
                            winner_u = min(sums, key=sums.get)
                            with self.lock:
                                self.stats[winner_u]["wins"] += 1
                                for u in lobby.hands:
                                    self.stats[u]["games"] += 1
                            lobby.broadcast({"game_over": {"blocked": True, "winner": winner_u, "sums": sums, "hands": lobby.hands}})
                            lobby.started = False
                            lobby.hands = {}
                            lobby.chain = []
                            lobby.turn_index = 0

                # --- request hand or lobby status ---
                elif action == "status":
                    lid = req.get("lobby_id")
                    lobby = self.lobbies.get(lid)
                    if not lobby:
                        conn.send(pickle.dumps({"error":"Lobby not found"}))
                        continue
                    with lobby.lock:
                        # send status to requester
                        owner_stats = self.stats.get(username, {"wins":0,"games":0})
                        user_hand = lobby.hands.get(username, [])
                        conn.send(pickle.dumps({"status": {"players": lobby.player_names, "chain": lobby.chain, "your_hand": user_hand, "turn": lobby.current_turn_username(), "hands_sizes": {u: len(h) for u,h in lobby.hands.items()}, "your_level": player_level(owner_stats["wins"], owner_stats["games"])}}))

                # --- heartbeat / ping ---
                elif action == "ping":
                    conn.send(pickle.dumps({"pong": time.time()}))

                else:
                    conn.send(pickle.dumps({"error":"Unknown action"}))

        except Exception as e:
            # unexpected error for a client
            #print("Client thread error:", e)
            pass
        finally:
            # cleanup on disconnect
            with self.lock:
                entry = self.clients.pop(conn, None)
            # remove from any lobby
            for lid, lobby in list(self.lobbies.items()):
                with lobby.lock:
                    for i,(c,uname,_) in enumerate(list(lobby.players)):
                        if c == conn:
                            lobby.players.pop(i)
                            lobby.player_names.pop(i)
                            lobby.broadcast({"lobby_update":{"players": lobby.player_names}})
            conn.close()

    def start(self):
        print(f"Starting server '{self.server_name}' on {self.host}:{self.port}")
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((self.host, self.port))
        self.sock.listen(64)
        try:
            while True:
                conn, addr = self.sock.accept()
                threading.Thread(target=self.client_thread, args=(conn, addr), daemon=True).start()
        except KeyboardInterrupt:
            print("Shutting down server.")
            self.running = False
            self.sock.close()


# --- Run server (ask initial settings interactively) ---
if __name__ == "__main__":
    HOST = "0.0.0.0"
    PORT = 5555
    print("=== Dominoes Server Setup ===")
    server_name = input("Server name (default 'DominoServer'): ").strip() or "DominoServer"
    try:
        max_players_per_lobby = int(input("Max players per lobby (2-6, default 4): ") or 4)
    except:
        max_players_per_lobby = 4
    try:
        max_lobbies = int(input("Max lobbies allowed (default 4): ") or 4)
    except:
        max_lobbies = 4
    difficulty = input("Default difficulty (easy/normal/hard) (default normal): ").strip().lower() or "normal"
    difficulty = difficulty if difficulty in ("easy","normal","hard") else "normal"
    server = GameServer(HOST, PORT, server_name, max_players_per_lobby, max_lobbies, difficulty)
    server.start()
