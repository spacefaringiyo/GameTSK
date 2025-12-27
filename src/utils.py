import json
import base64
import zlib
import hashlib

PROTOCOL_PREFIX = "TSK1:"

def generate_hash(config_data):
    """
    Creates a unique ID for a setting configuration.
    Sorts keys to ensure {a:1, b:2} produces same hash as {b:2, a:1}
    """
    # Create a clean copy with only physics params
    clean = {
        "smoothing": config_data.get("smoothing"),
        "zoom_scale": config_data.get("zoom_scale"),
        "start_speed": config_data.get("start_speed"),
        "end_speed": config_data.get("end_speed"),
        "tolerance": config_data.get("tolerance"),
        "duration": config_data.get("duration"),
        "warmup_time": config_data.get("warmup_time"),
        "directions": config_data.get("directions", [True, True, True, True])
    }
    
    # Dump to string, consistent sorting
    s = json.dumps(clean, sort_keys=True)
    return hashlib.md5(s.encode('utf-8')).hexdigest()

def encode_config(config_data):
    """
    JSON -> String -> Zip -> Base64 -> TSK1:...
    """
    try:
        # 1. Clean data (remove names/hashes, keep physics)
        clean = {k: v for k, v in config_data.items() if k not in ['name', 'hash', 'date']}
        
        # 2. JSON String
        json_str = json.dumps(clean)
        
        # 3. Compress
        compressed = zlib.compress(json_str.encode('utf-8'))
        
        # 4. Base64
        b64 = base64.b64encode(compressed).decode('utf-8')
        
        return PROTOCOL_PREFIX + b64
    except Exception as e:
        print(f"Encode Error: {e}")
        return None

def decode_config(code_str):
    """
    TSK1:... -> Base64 -> Unzip -> JSON Dict
    """
    try:
        code_str = code_str.strip()
        if not code_str.startswith(PROTOCOL_PREFIX):
            return None
        
        payload = code_str[len(PROTOCOL_PREFIX):]
        
        # 1. Base64 Decode
        compressed = base64.b64decode(payload)
        
        # 2. Decompress
        json_str = zlib.decompress(compressed).decode('utf-8')
        
        # 3. JSON Load (FIXED: loads instead of load)
        return json.loads(json_str) 
        
    except Exception as e:
        print(f"Decode Error: {e}")
        return None

def generate_auto_name(data):
    """
    Format: [DIR] [SPEED] ±[TOL] (sm[S] z[Z] b[B] [D]s)
    Example: ↔ 500→1000 ±50 (sm15 z3 b0 15s)
    """
    s = data.get('start_speed', 0)
    e = data.get('end_speed', 0)
    d = int(data.get('duration', 15))
    t = int(data.get('tolerance', 50))
    sm = int(data.get('smoothing', 15))
    z = int(data.get('zoom_scale', 3))
    b = int(data.get('warmup_time', 0))
    
    # 1. Decode Directions
    dirs = data.get('directions', [True, True, True, True])
    up, down, left, right = dirs[0], dirs[1], dirs[2], dirs[3]
    count = sum(dirs)
    
    dir_str = ""
    
    # Special Cases for clean look
    if count == 4:
        dir_str = "✥" # Omni
    elif count == 0:
        dir_str = "Ø" # None
    elif left and right and not up and not down:
        dir_str = "↔" # Horizontal
    elif up and down and not left and not right:
        dir_str = "↕" # Vertical
    else:
        # Build Combo (e.g. ↑→)
        # Order: U D L R
        if up: dir_str += "↑"
        if down: dir_str += "↓"
        if left: dir_str += "←"
        if right: dir_str += "→"

    # 2. Decode Speed
    if s == e:
        spd_str = f"{s}"
    else:
        spd_str = f"{s}→{e}"

    # 3. Assemble
    # Main: Dir, Speed, Tolerance
    main_part = f"{dir_str} {spd_str} ±{t}"
    
    # Meta: Smoothing, Zoom, Buffer, Duration
    meta_part = f"(sm{sm} z{z} b{b} {d}s)"
    
    return f"{main_part} {meta_part}"