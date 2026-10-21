from flask import Flask, render_template_string
from flask_socketio import SocketIO
from pynput.mouse import Controller as MouseController, Button
from pynput.keyboard import Controller as KeyboardController, Key

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*") 
mouse = MouseController()
keyboard = KeyboardController()

HTML_PAGE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Dev Remote Pro</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/socket.io/4.0.1/socket.io.js"></script>
    <style>
        body, html { 
            margin: 0; padding: 0; width: 100%; height: 100%; 
            background-color: #1a1a1a; color: white; font-family: sans-serif; overflow: hidden; 
            -webkit-touch-callout: none; -webkit-user-select: none; user-select: none; 
        }
        
        .container { display: flex; height: 60%; width: 100%; }
        
        #trackpad { flex: 4; background-color: #2a2a2a; border-radius: 10px 0 0 10px; display: flex; align-items: center; justify-content: center; touch-action: none; border-right: 2px solid #444; transition: background-color 0.1s ease; }
        #trackpad.active-touch { background-color: #3d3d3d; }
        
        #scrollzone { flex: 1; background-color: #333; border-radius: 0 10px 10px 0; display: flex; align-items: center; justify-content: center; touch-action: none; font-size: 12px; color: #888; writing-mode: vertical-rl; transition: background-color 0.1s ease; }
        #scrollzone.active-touch { background-color: #4a4a4a; }

        .controls-wrapper { display: flex; flex-direction: column; height: 40%; width: 100%; }
        .buttons-row { display: grid; grid-template-columns: 1fr 1fr 1.2fr 1fr; height: 50%; }
        .arrows-row { display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; height: 50%; }
        
        .btn { border: 1px solid #1a1a1a; background-color: #333; font-size: 16px; font-weight: bold; color: white; touch-action: manipulation; transition: all 0.1s; outline: none; }
        .btn:active { background-color: #555; }
        .btn.active-modifier { background-color: #007acc; border-color: #005999; }
        
        .arrow-btn { font-size: 22px; background-color: #222; }
        
        #hidden-input { position: absolute; top: -100px; left: -100px; opacity: 0; pointer-events: none; -webkit-user-select: text; user-select: text; }
    </style>
</head>
<body>
    <input type="text" id="hidden-input" autocomplete="off" autocorrect="off" autocapitalize="off" spellcheck="false">
    <div class="container">
        <div id="trackpad">MOVE / DRAG</div>
        <div id="scrollzone">SCROLL</div>
    </div>
    <div class="controls-wrapper">
        <div class="buttons-row">
            <button class="btn" id="ctrl-btn" onclick="toggleCtrl()">CTRL</button>
            <button class="btn" onclick="sendClick('left', 1)">L-CLK</button>
            <button class="btn" onclick="openKeyboard()">KEYBD</button>
            <button class="btn" onclick="sendClick('right', 1)">R-CLK</button>
        </div>
        <div class="arrows-row">
            <button class="btn arrow-btn" ontouchstart="startKey(event, 'left')" ontouchend="stopKey(event)" ontouchcancel="stopKey(event)">◀</button>
            <button class="btn arrow-btn" ontouchstart="startKey(event, 'up')" ontouchend="stopKey(event)" ontouchcancel="stopKey(event)">▲</button>
            <button class="btn arrow-btn" ontouchstart="startKey(event, 'down')" ontouchend="stopKey(event)" ontouchcancel="stopKey(event)">▼</button>
            <button class="btn arrow-btn" ontouchstart="startKey(event, 'right')" ontouchend="stopKey(event)" ontouchcancel="stopKey(event)">▶</button>
        </div>
    </div>

    <script>
        const socket = io();
        const pad = document.getElementById('trackpad');
        const scroll = document.getElementById('scrollzone');
        const input = document.getElementById('hidden-input');
        const ctrlBtn = document.getElementById('ctrl-btn');
        
        let lastX = 0, lastY = 0, lastScrollY = 0;
        let lastTap = 0, moved = false, isDragging = false, potentialDrag = false;
        
        // --- MODIFIER LOGIC ---
        let ctrlLatching = false;

        function toggleCtrl() {
            ctrlLatching = !ctrlLatching;
            if (ctrlLatching) ctrlBtn.classList.add('active-modifier');
            else ctrlBtn.classList.remove('active-modifier');
            input.focus();
        }

        function consumeCtrl() {
            let wasActive = ctrlLatching;
            if (ctrlLatching) {
                ctrlLatching = false;
                ctrlBtn.classList.remove('active-modifier');
            }
            return wasActive;
        }

        // --- KEYBOARD & REPEATING ARROWS LOGIC ---
        function openKeyboard() { 
            input.value = ' '; 
            input.focus(); 
        }

        function sendKey(keyName) {
            socket.emit('key_press', {key: keyName, ctrl: consumeCtrl()});
        }

        // Timer variables for the hold-to-repeat loop
        let keyTimer, keyInterval;

        function startKey(e, keyName) {
            e.preventDefault(); // Stop iOS from doing weird highlight stuff
            sendKey(keyName); // Fire once instantly
            
            // Wait 400ms to see if they are holding it down
            keyTimer = setTimeout(() => {
                // If held down, rapid fire every 50ms
                keyInterval = setInterval(() => {
                    // Pass false for ctrl so it doesn't unlatch repeatedly if they are holding Ctrl+Arrow
                    socket.emit('key_press', {key: keyName, ctrl: ctrlLatching}); 
                }, 50);
            }, 400);
        }

        function stopKey(e) {
            e.preventDefault();
            clearTimeout(keyTimer);
            clearInterval(keyInterval);
        }

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') { e.preventDefault(); sendKey('enter'); } 
            else if (e.key === 'Backspace') { sendKey('backspace'); }
        });

        input.addEventListener('input', (e) => {
            if (e.inputType === 'deleteContentBackward' || input.value.length === 0) { sendKey('backspace'); } 
            else if (e.data) { sendKey(e.data); }
            input.value = ' '; 
        });

        function flashPad() {
            pad.classList.add('active-touch');
            setTimeout(() => { pad.classList.remove('active-touch'); }, 150);
        }

        // --- TRACKPAD LOGIC ---
        pad.addEventListener('touchstart', (e) => {
            e.preventDefault(); 
            let now = Date.now();
            if (now - lastTap < 300) { potentialDrag = true; } 
            else { potentialDrag = false; }
            lastX = e.touches[0].clientX; lastY = e.touches[0].clientY;
            moved = false;
        });

        pad.addEventListener('touchmove', (e) => {
            e.preventDefault(); 
            if (potentialDrag && !isDragging) {
                isDragging = true;
                pad.classList.add('active-touch'); 
                socket.emit('drag_start'); 
            }
            moved = true;
            let dx = (e.touches[0].clientX - lastX) * 7;
            let dy = (e.touches[0].clientY - lastY) * 7;
            socket.emit('move', {dx: dx, dy: dy});
            lastX = e.touches[0].clientX; lastY = e.touches[0].clientY;
        });

        pad.addEventListener('touchend', (e) => {
            e.preventDefault();
            if (isDragging) { 
                socket.emit('drag_end'); 
                isDragging = false; potentialDrag = false; lastTap = 0; 
                pad.classList.remove('active-touch'); 
            } else if (!moved) {
                flashPad(); 
                let now = Date.now();
                if (potentialDrag) {
                    socket.emit('click', {button: 'left', count: 2, ctrl: consumeCtrl()}); 
                    potentialDrag = false; lastTap = 0;
                } else {
                    socket.emit('click', {button: 'left', count: 1, ctrl: consumeCtrl()}); 
                    lastTap = now;
                }
            }
        });
        
        pad.addEventListener('touchcancel', (e) => { pad.classList.remove('active-touch'); });

        // --- SCROLL LOGIC ---
        scroll.addEventListener('touchstart', (e) => { 
            e.preventDefault(); scroll.classList.add('active-touch'); lastScrollY = e.touches[0].clientY; 
        });
        scroll.addEventListener('touchmove', (e) => {
            e.preventDefault();
            let dy = (e.touches[0].clientY - lastScrollY) * -0.5;
            socket.emit('scroll', {dy: dy});
            lastScrollY = e.touches[0].clientY;
        });
        scroll.addEventListener('touchend', (e) => { scroll.classList.remove('active-touch'); });
        scroll.addEventListener('touchcancel', (e) => { scroll.classList.remove('active-touch'); });

        function sendClick(buttonType, count) { 
            socket.emit('click', {button: buttonType, count: count, ctrl: consumeCtrl()}); 
        }
        
        document.addEventListener('contextmenu', event => event.preventDefault());
    </script>
</body>
</html>
"""

@app.route('/')
def index(): return render_template_string(HTML_PAGE)

@socketio.on('move')
def handle_move(data): mouse.move(data['dx'], data['dy'])

@socketio.on('scroll')
def handle_scroll(data): mouse.scroll(0, data['dy'])

@socketio.on('click')
def handle_click(data):
    btn = Button.left if data['button'] == 'left' else Button.right
    if data.get('ctrl'): keyboard.press(Key.ctrl)
    mouse.click(btn, data['count'])
    if data.get('ctrl'): keyboard.release(Key.ctrl)

@socketio.on('drag_start')
def handle_drag_start(): mouse.press(Button.left)

@socketio.on('drag_end')
def handle_drag_end(): mouse.release(Button.left)

@socketio.on('key_press')
def handle_key(data):
    key_map = {
        'backspace': Key.backspace, 'enter': Key.enter,
        'up': Key.up, 'down': Key.down,
        'left': Key.left, 'right': Key.right
    }
    val = data['key']
    if isinstance(val, str) and len(val) == 1: val = val.lower()
    if val in key_map: val = key_map[val]

    if data.get('ctrl'): keyboard.press(Key.ctrl)

    try:
        if isinstance(val, str) and len(val) > 1: keyboard.type(val)
        else:
            keyboard.press(val)
            keyboard.release(val)
    except Exception as e:
        print(f"Key error: {e}")

    if data.get('ctrl'): keyboard.release(Key.ctrl)

if __name__ == '__main__':
    socketio.run(app, host='192.168.137.1', port=5000)