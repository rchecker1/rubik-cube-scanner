import cv2
import numpy as np
import twophase.solver as sv

def colorconvert(colorstring):
    cubestring = ''
    for i in range(54):
        if colorstring[i] == 'W':
            cubestring += 'U'
        elif colorstring[i] == 'Y':
            cubestring += 'D'
        elif colorstring[i] == 'O':
            cubestring += 'B'
        elif colorstring[i] == 'B':
            cubestring += 'R'
        elif colorstring[i] == 'G':
            cubestring += 'L'
        elif colorstring[i] == 'R':
            cubestring += 'F'
    print(cubestring)
    return cubestring

def detect_color(bgr_color):
    b, g, r = bgr_color
    hsv = cv2.cvtColor(np.uint8([[[b, g, r]]]), cv2.COLOR_BGR2HSV)[0][0]
    h, s, v = hsv
    
    # white is bright and not very colorful
    if v > 160 and s < 60:
        return 'W'
    
    # yellow hue around 25-35
    elif 22 <= h <= 38 and s > 80 and v > 100:
        return 'Y'
    
    # orange is between red and yellow
    elif 5 <= h <= 30 and s > 80:
        return 'O'
    
    # red wraps around the hue circle, must calibrate
    elif (h <= 8 or h >= 170) and s > 90:
        return 'R'
    
    # green is color usually around here
    elif 45 <= h <= 75 and s > 70:
        return 'G'
    
    # blue 
    elif 100 <= h <= 125 and s > 70:
        return 'B'
    
    # backup plan if hsv does not work
    else:
        if r > g + 30 and r > b + 30:
            return 'R'
        elif g > r + 30 and g > b + 30:
            return 'G'
        elif b > r + 30 and b > g + 30:
            return 'B'
        elif v > 150:
            return 'W'
        else:
            return 'Y'  # when in doubt

def identify_face_by_center(face_colors):
    if not face_colors or len(face_colors) != 9:
        return None
    
    center_color = face_colors[4]  # center square
    
    face_mapping = {
        'W': 'TOP',
        'G': 'LEFT',
        'R': 'FRONT',
        'Y': 'BOTTOM',
        'B': 'RIGHT',
        'O': 'BACK'
    }
    
    return face_mapping.get(center_color, 'UNKNOWN')

def scan_single_face():
    cap = cv2.VideoCapture(1)
    
    if not cap.isOpened():
        print("camera not working")
        return None
    
    face_colors = []
    captured = False
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
            
        height, width = frame.shape[:2]
        
        # setup 3x3 grid
        grid_size = 300
        start_x = width // 2 - grid_size // 2
        start_y = height - grid_size - 30
        
        colors = []
        for row in range(3):
            for col in range(3):
                x1 = start_x + col * (grid_size // 3)
                y1 = start_y + row * (grid_size // 3)
                x2 = x1 + (grid_size // 3)
                y2 = y1 + (grid_size // 3)
                
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 0), 2)
                
                center_x = (x1 + x2) // 2
                center_y = (y1 + y2) // 2
                bgr_color = frame[center_y, center_x]
                
                color = detect_color(bgr_color)
                colors.append(color)
                
                cv2.putText(frame, color, (center_x - 10, center_y + 5), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 2)
        
        # show different message if captured
        if captured:
            cv2.putText(frame, f"CAPTURED: {''.join(face_colors)} - press ENTER to confirm", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        else:
            cv2.putText(frame, "position cube face in grid, space to capture", 
                       (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        cv2.putText(frame, "q to quit", 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 0), 2)
        
        cv2.imshow('cube scanner', frame)
        
        key = cv2.waitKey(30) & 0xFF
        if key == ord(' ') and not captured:
            face_colors = colors.copy()
            captured = True
            print(f"captured: {''.join(colors)}")
        elif key == ord('\r') and captured:  # enter key
            break
        elif key == ord('q'):
            face_colors = None
            break
    
    cap.release()
    cv2.destroyAllWindows()
    return face_colors

def flexible_cube_scanner():
    print("cube scanner starting")
    
    all_faces = {}
    required_faces = ['TOP', 'RIGHT', 'FRONT', 'BOTTOM', 'LEFT', 'BACK']
    
    face_count = 0
    
    while len(all_faces) < 6:
        face_count += 1
        print(f"\nscanning face {face_count}")
        print("position any face toward camera")
        
        # show whats missing
        missing_faces = [face for face in required_faces if face not in all_faces]
        if missing_faces:
            print(f"still need: {', '.join(missing_faces)}")
        
        input("press enter when ready...")
        
        face_colors = scan_single_face()
        if not face_colors:
            print("scan failed, try again")
            face_count -= 1
            continue
        
        face_name = identify_face_by_center(face_colors)
        
        if face_name == 'UNKNOWN':
            print(f"unknown center color: {face_colors[4]}")
            face_count -= 1
            continue
        
        if face_name in all_faces:
            print(f"already scanned {face_name}")
            print("try different face")
            face_count -= 1
            continue
        
        all_faces[face_name] = face_colors
        print(f"identified as {face_name}")
        print(f"colors: {''.join(face_colors)}")
        
        completed = list(all_faces.keys())
        remaining = [face for face in required_faces if face not in completed]
        print(f"completed: {', '.join(completed)}")
        if remaining:
            print(f"remaining: {', '.join(remaining)}")
    
    print("\nall faces scanned")
    
    # build the string in right order
    ordered_faces = ['TOP', 'RIGHT', 'FRONT', 'BOTTOM', 'LEFT', 'BACK']
    cube_string = ""
    
    for face_name in ordered_faces:
        face_colors = all_faces[face_name]
        cube_string += ''.join(face_colors)
        print(f"{face_name}: {''.join(face_colors)}")
    
    print(f"\ncomplete cube: {cube_string}")
    
    # convert and solve
    try:
        converted_string = colorconvert(cube_string)
        print(f"converted: {converted_string}")
        
        solution = sv.solve(converted_string, 20, 3)
        print(f"\nraw solution: {solution}")
        print_readable_solution(solution)
    except Exception as e:
        print(f"error solving: {e}")
        print("cube state might be invalid")
    
    return cube_string
def convert_solution_to_readable(solution_string):
    """
    turn default sv codes to readable
    """
    
    # face mappings with colors
    face_names = {
        'L': 'LEFT/GREEN',
        'D': 'DOWN/YELLOW', 
        'B': 'BACK/ORANGE',
        'R': 'RIGHT/BLUE',
        'U': 'UP/WHITE',
        'F': 'FRONT/RED'  
    }
    
    # direction mappings
    directions = {
        '1': 'clockwise 90°',
        '2': '180°', 
        '3': 'counter-clockwise 90°'
    }
    
    # clean up the solution string
    moves = solution_string.replace('(', '').replace(')', '').split()
    # remove the last part like "20f" if it exists
    moves = [move for move in moves if not move.endswith('f')]
    
    readable_moves = []
    
    for move in moves:
        if len(move) >= 2:
            face = move[0]
            direction = move[1]
            
            if face in face_names and direction in directions:
                face_name = face_names[face]
                direction_name = directions[direction]
                readable_moves.append(f"{face_name} {direction_name}")
    
    return readable_moves

def print_readable_solution(solution):
    """Print solution in a nice readable format"""
    readable = convert_solution_to_readable(solution)
    
    print("\n" + "-:"*50)
    print("RUBIK'S CUBE SOLUTION")
    print("-:"*50)
    
    for i, move in enumerate(readable, 1):
        print(f"{i:2d}. {move}")
    
    print("-:"*50)
    print(f"Total moves: {len(readable)}")
    print("-:"*50)

flexible_cube_scanner()