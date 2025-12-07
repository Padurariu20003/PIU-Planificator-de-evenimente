import math

LOGICAL_WIDTH = 1600
LOGICAL_HEIGHT = 900


def rotate_point(cx, cy, x, y, angle_deg):
    rad = math.radians(angle_deg)
    tx = x - cx
    ty = y - cy
    rx = tx * math.cos(rad) - ty * math.sin(rad)
    ry = tx * math.sin(rad) + ty * math.cos(rad)
    return rx + cx, ry + cy


def apply_rotation_to_group(items, center_x, center_y, angle):
    if angle == 0: return items
    for item in items:
        ix = item['x'] + item['w'] / 2
        iy = item['y'] + item['h'] / 2
        nx, ny = rotate_point(center_x, center_y, ix, iy, angle)
        item['x'] = nx - item['w'] / 2
        item['y'] = ny - item['h'] / 2
        item['rotation'] = (item.get('rotation', 0) + angle) % 360
    return items


def center_layout(items, scene_w=LOGICAL_WIDTH, scene_h=LOGICAL_HEIGHT):
    if not items: return items
    min_x = min(i['x'] for i in items)
    max_x = max(i['x'] + i['w'] for i in items)
    min_y = min(i['y'] for i in items)
    max_y = max(i['y'] + i['h'] for i in items)

    group_w = max_x - min_x
    group_h = max_y - min_y

    off_x = (scene_w - group_w) / 2 - min_x
    off_y = (scene_h - group_h) / 2 - min_y

    for i in items:
        i['x'] += off_x
        i['y'] += off_y
    return items


def generate_decor(x, y, type_decor, w=100, h=50, label="Decor", rotation=0):
    return [{
        "id": f"D-{label}", "type": type_decor,
        "x": x - w / 2, "y": y - h / 2, "w": w, "h": h,
        "label": label, "rotation": rotation
    }]


def generate_round_table_set(center_x, center_y, table_id, num_seats=8):
    items = []
    table_radius = max(25, 5 + (num_seats * 4))
    seat_distance = table_radius + 20

    items.append({
        "id": table_id, "type": "table_round",
        "x": center_x - table_radius, "y": center_y - table_radius,
        "w": table_radius * 2, "h": table_radius * 2, "rotation": 0
    })

    for i in range(num_seats):
        angle = (2 * math.pi / num_seats) * i
        sx = center_x + math.cos(angle) * seat_distance
        sy = center_y + math.sin(angle) * seat_distance
        seat_rot = math.degrees(angle) + 90
        items.append({
            "id": f"{table_id}-{i + 1}", "type": "seat",
            "x": sx - 15, "y": sy - 15, "w": 30, "h": 30,
            "parent_id": table_id, "rotation": seat_rot
        })
    return items


def generate_rect_table_set(center_x, center_y, table_id, num_seats=6, is_square=False):
    items = []
    seat_w = 30
    seat_gap = 5
    side_seats = math.ceil(num_seats / 2)

    if is_square:
        t_width = max(50, side_seats * (seat_w + seat_gap) + 10)
        t_height = t_width
    else:
        t_width = max(70, side_seats * (seat_w + seat_gap) + 20)
        t_height = 60

    t_x = center_x - t_width / 2
    t_y = center_y - t_height / 2

    items.append({
        "id": table_id, "type": "table_rect",
        "x": t_x, "y": t_y, "w": t_width, "h": t_height, "rotation": 0
    })

    spacing = t_width / (side_seats + 1)
    for i in range(side_seats):
        sx = t_x + spacing * (i + 1) - (seat_w / 2)
        sy = t_y - 32
        if (i + 1) <= num_seats:
            items.append(
                {"id": f"{table_id}-{i + 1}", "type": "seat", "x": sx, "y": sy, "w": 30, "h": 30, "parent_id": table_id,
                 "rotation": 0})
    for i in range(side_seats):
        sx = t_x + spacing * (i + 1) - (seat_w / 2)
        sy = t_y + t_height + 2
        seat_num = side_seats + i + 1
        if seat_num <= num_seats:
            items.append({"id": f"{table_id}-{seat_num}", "type": "seat", "x": sx, "y": sy, "w": 30, "h": 30,
                          "parent_id": table_id, "rotation": 180})
    return items


def generate_seat_block(start_x, start_y, rows, cols, start_row_char='A', start_col_num=1):
    items = []
    seat_size = 30
    gap = 5
    for r in range(rows):
        row_char = chr(ord(start_row_char) + r)
        for c in range(cols):
            items.append({
                "id": f"{row_char}{start_col_num + c}", "type": "seat",
                "x": start_x + c * (seat_size + gap),
                "y": start_y + r * (seat_size + gap),
                "w": seat_size, "h": seat_size, "rotation": 0
            })
    return items



def create_cinema_template(rows=8, cols_per_side=6):
    items = []

    seat_w = 30
    gap = 5
    block_width = cols_per_side * (seat_w + gap) - gap
    aisle_width = 60
    total_width = block_width * 2 + aisle_width

    # 1. Ecranul
    screen_w = total_width * 0.8
    items.extend(generate_decor(total_width / 2, 0, "decor_screen", screen_w, 20, "ECRAN"))

    # 2. Scaune
    start_y = 100
    items.extend(generate_seat_block(0, start_y, rows, cols_per_side, 'A', 1))
    items.extend(generate_seat_block(block_width + aisle_width, start_y, rows, cols_per_side, 'A', cols_per_side + 1))

    # 3. Intrare
    items.extend(generate_decor(total_width / 2, start_y + rows * 40 + 50, "decor_generic", 120, 40, "INTRARE"))

    return center_layout(items)


def create_conference_template():
    items = []

    # 1. Scena + Prezidiu
    items.extend(generate_decor(500, 0, "decor_stage", 600, 100, "SCENA"))
    items.extend(generate_decor(500, 20, "decor_generic", 400, 40, "PREZIDIU"))

    # 2. Scaune Sala
    rows = 10
    cols_side = 8

    items.extend(generate_seat_block(100, 180, rows, cols_side, 'A', 1))
    items.extend(generate_seat_block(100 + (cols_side * 35) + 60, 180, rows, cols_side, 'A', cols_side + 1))

    # 3. Ecran Proiectie
    items.extend(generate_decor(50, 50, "decor_screen", 150, 10, "ECRAN S", rotation=20))
    items.extend(generate_decor(950, 50, "decor_screen", 150, 10, "ECRAN D", rotation=-20))

    # 4. Intrare
    items.extend(generate_decor(500, 180 + rows * 40 + 50, "decor_generic", 120, 40, "INTRARE"))

    return center_layout(items)


def create_wedding_template(size="large"):
    items = []

    # 1. Scena + DJ
    items.extend(generate_decor(800, 0, "decor_stage", 400, 100, "SCENA LIVE"))
    items.extend(generate_decor(1100, 50, "decor_generic", 100, 60, "DJ"))

    # 2. Ring Dans
    items.extend(generate_decor(800, 250, "decor_generic", 400, 300, "DANCE FLOOR"))

    # 3. Masa miri
    items.extend(generate_rect_table_set(800, 600, "M_MIRI", 4, False))

    # 4. Mese invitati
    if size == "large":
        positions = [
            (200, 100), (450, 100), (1350, 100), (1600, 100),
            (200, 350), (450, 350), (1350, 350), (1600, 350),
            (200, 600), (450, 600), (1350, 600), (1600, 600)
        ]
    else:
        positions = [
            (300, 200), (1300, 200),
            (300, 450), (1300, 450),
            (300, 700), (1300, 700)
        ]

    for i, (x, y) in enumerate(positions):
        items.extend(generate_round_table_set(x, y, f"M{i + 1}", 10 if size == "large" else 8))

    # 5. Facilitati (bar, bufet, intrare)
    items.extend(generate_decor(100, 800, "decor_bar", 200, 60, "BAR"))
    items.extend(generate_decor(1500, 800, "decor_generic", 250, 60, "BUFET SUEDEZ"))
    items.extend(generate_decor(800, 850, "decor_generic", 150, 50, "INTRARE"))

    return center_layout(items)


def create_club_layout():
    items = []

    # Ring central
    items.extend(generate_decor(800, 450, "decor_generic", 300, 300, "DANCE"))

    # Bar
    items.extend(generate_decor(800, 50, "decor_bar", 400, 80, "MAIN BAR"))

    # DJ Booth
    items.extend(generate_decor(800, 250, "decor_generic", 100, 50, "DJ"))

    # VIP Booths
    for i in range(4):
        items.extend(generate_rect_table_set(150, 200 + i * 150, f"VIP-L{i + 1}", 4, True))
    for i in range(4):
        items.extend(generate_rect_table_set(1450, 200 + i * 150, f"VIP-R{i + 1}", 4, True))

    # Mese
    for i in range(6):
        x = 400 + i * 160
        items.extend(generate_round_table_set(x, 750, f"T{i + 1}", 2))

    items.extend(generate_decor(800, 900, "decor_generic", 120, 40, "INTRARE"))

    return center_layout(items)