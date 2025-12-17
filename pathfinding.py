import heapq
from constants import GRID_SIZE

def a_star_search(start, goal, obstacles):
    """
    Znajduje ścieżkę z punktu start (x,y) do goal (x,y).
    obstacles: zbiór (set) krotek (x,y), których nie można przekroczyć.
    """
    open_set = []
    heapq.heappush(open_set, (0, start))
    
    came_from = {}
    g_score = {start: 0}
    f_score = {start: abs(start[0] - goal[0]) + abs(start[1] - goal[1])} # Heurystyka Manhattan
    
    while open_set:
        current = heapq.heappop(open_set)[1]
        
        if current == goal:
            # Odtwarzanie ścieżki
            path = []
            while current in came_from:
                path.append(current)
                current = came_from[current]
            path.reverse() # Odwracamy, żeby mieć od startu do celu
            return path
        
        # Sąsiedzi (Góra, Dół, Lewo, Prawo)
        neighbors = [
            (current[0], current[1]-1), (current[0], current[1]+1),
            (current[0]-1, current[1]), (current[0]+1, current[1])
        ]
        
        for neighbor in neighbors:
            nx, ny = neighbor
            # Sprawdzenie granic mapy
            if 0 <= nx < GRID_SIZE and 0 <= ny < GRID_SIZE:
                # Sprawdzenie przeszkód (chyba że to cel)
                if neighbor in obstacles and neighbor != goal:
                    continue
                    
                tentative_g_score = g_score[current] + 1
                
                if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                    came_from[neighbor] = current
                    g_score[neighbor] = tentative_g_score
                    f = tentative_g_score + abs(nx - goal[0]) + abs(ny - goal[1])
                    f_score[neighbor] = f
                    heapq.heappush(open_set, (f, neighbor))
                    
    return [] # Brak ścieżki