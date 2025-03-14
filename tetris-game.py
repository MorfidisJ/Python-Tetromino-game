import pygame
import random
import time
from collections import deque

# Initialize pygame
pygame.init()

# Constants
SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 900
BLOCK_SIZE = 30
GRID_WIDTH = 10
GRID_HEIGHT = 20
GRID_OFFSET_X = (SCREEN_WIDTH - GRID_WIDTH * BLOCK_SIZE) // 2
GRID_OFFSET_Y = (SCREEN_HEIGHT - GRID_HEIGHT * BLOCK_SIZE) // 2

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GRAY = (128, 128, 128)
DARK_GRAY = (40, 40, 40)
CYAN = (0, 255, 255)   # I piece
BLUE = (0, 0, 255)     # J piece
ORANGE = (255, 165, 0) # L piece
YELLOW = (255, 255, 0) # O piece
GREEN = (0, 255, 0)    # S piece
PURPLE = (128, 0, 128) # T piece
RED = (255, 0, 0)      # Z piece

# Tetromino shapes and colors
SHAPES = [
    [[1, 1, 1, 1]],  # I
    [[1, 0, 0], [1, 1, 1]],  # J
    [[0, 0, 1], [1, 1, 1]],  # L
    [[1, 1], [1, 1]],  # O
    [[0, 1, 1], [1, 1, 0]],  # S
    [[0, 1, 0], [1, 1, 1]],  # T
    [[1, 1, 0], [0, 1, 1]]   # Z
]

COLORS = [CYAN, BLUE, ORANGE, YELLOW, GREEN, PURPLE, RED]

# Set up the screen
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Tetris")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 36)
small_font = pygame.font.SysFont(None, 24)

class Tetromino:
    def __init__(self, x, y, shape_index):
        self.x = x
        self.y = y
        self.shape_index = shape_index
        self.shape = SHAPES[shape_index]
        self.color = COLORS[shape_index]
        self.rotation = 0

    def rotate(self):
        # Transpose the matrix and reverse each row to rotate 90 degrees clockwise
        rows = len(self.shape)
        cols = len(self.shape[0])
        rotated = [[self.shape[rows - 1 - j][i] for j in range(rows)] for i in range(cols)]
        return rotated

    def get_rotated_shape(self):
        shape = self.shape
        for _ in range(self.rotation % 4):
            shape = self.rotate_shape(shape)
        return shape

    def rotate_shape(self, shape):
        # Transpose the matrix and reverse each row to rotate 90 degrees clockwise
        rows = len(shape)
        cols = len(shape[0])
        rotated = [[shape[rows - 1 - j][i] for j in range(rows)] for i in range(cols)]
        return rotated

class PieceGenerator:
    def __init__(self, max_consecutive=2):
        self.max_consecutive = max_consecutive
        self.recent_pieces = deque(maxlen=max_consecutive)
        self.bag = list(range(len(SHAPES)))
        random.shuffle(self.bag)
    
    def get_next_piece(self):
        # If bag is empty, refill it
        if not self.bag:
            self.bag = list(range(len(SHAPES)))
            random.shuffle(self.bag)
        
        # Check if we need to prevent a third consecutive piece
        if len(self.recent_pieces) == self.max_consecutive and len(set(self.recent_pieces)) == 1:
            repeat_piece = self.recent_pieces[0]
            
            # Remove the repeat piece from the bag if it's there
            if repeat_piece in self.bag:
                self.bag.remove(repeat_piece)
                
            # If bag is now empty (unlikely but possible), refill it without the repeat piece
            if not self.bag:
                self.bag = [i for i in range(len(SHAPES)) if i != repeat_piece]
                random.shuffle(self.bag)
        
        # Get next piece from the bag
        piece_index = self.bag.pop(0)
        
        # Update the recent pieces record
        self.recent_pieces.append(piece_index)
        
        return piece_index

class TetrisGame:
    def __init__(self):
        self.piece_generator = PieceGenerator(max_consecutive=2)
        self.reset_game()

    def reset_game(self):
        self.grid = [[0 for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        self.piece_generator = PieceGenerator(max_consecutive=2)
        self.current_piece = self.new_piece()
        self.next_piece = self.new_piece()
        self.hold_piece = None
        self.can_hold = True
        self.game_over = False
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.fall_speed = 0.5  # seconds per step
        self.fall_timer = 0
        self.fast_fall = False
        # Initialize timer
        self.start_time = time.time()
        self.elapsed_time = 0
        self.paused = False

    def new_piece(self):
        # Create a new random tetromino using the piece generator
        shape_index = self.piece_generator.get_next_piece()
        return Tetromino(GRID_WIDTH // 2 - 1, 0, shape_index)

    def hold(self):
        if not self.can_hold:
            return
        
        if self.hold_piece is None:
            # Store current piece and get next piece
            self.hold_piece = Tetromino(GRID_WIDTH // 2 - 1, 0, self.current_piece.shape_index)
            self.current_piece = self.next_piece
            self.next_piece = self.new_piece()
        else:
            # Swap current piece with hold piece
            temp = self.current_piece.shape_index
            self.current_piece = Tetromino(GRID_WIDTH // 2 - 1, 0, self.hold_piece.shape_index)
            self.hold_piece = Tetromino(GRID_WIDTH // 2 - 1, 0, temp)
        
        # Reset rotation of current piece
        self.current_piece.rotation = 0
        
        # Disable hold until piece is placed
        self.can_hold = False

    def valid_position(self, piece, x, y, rotation):
        shape = piece.shape
        for _ in range(rotation % 4):
            shape = piece.rotate_shape(shape)
        
        for i in range(len(shape)):
            for j in range(len(shape[0])):
                if shape[i][j] == 0:
                    continue
                
                # Check if out of bounds
                if y + i >= GRID_HEIGHT or x + j < 0 or x + j >= GRID_WIDTH:
                    return False
                
                # Check if collides with existing blocks
                if y + i >= 0 and self.grid[y + i][x + j] != 0:
                    return False
        
        return True

    def rotate_piece(self):
        new_rotation = (self.current_piece.rotation + 1) % 4
        if self.valid_position(self.current_piece, self.current_piece.x, self.current_piece.y, new_rotation):
            self.current_piece.rotation = new_rotation

    def move_piece(self, dx, dy):
        if self.valid_position(self.current_piece, self.current_piece.x + dx, self.current_piece.y + dy, self.current_piece.rotation):
            self.current_piece.x += dx
            self.current_piece.y += dy
            return True
        return False

    def drop_piece(self):
        while self.move_piece(0, 1):
            pass
        self.place_piece()

    def place_piece(self):
        shape = self.current_piece.shape
        for _ in range(self.current_piece.rotation % 4):
            shape = self.current_piece.rotate_shape(shape)
        
        for i in range(len(shape)):
            for j in range(len(shape[0])):
                if shape[i][j] == 0:
                    continue
                
                # Place the block on the grid
                if self.current_piece.y + i >= 0:
                    self.grid[self.current_piece.y + i][self.current_piece.x + j] = self.current_piece.shape_index + 1
        
        # Check for cleared lines
        self.check_clear_lines()
        
        # Get next piece
        self.current_piece = self.next_piece
        self.next_piece = self.new_piece()
        
        # Reset hold capability
        self.can_hold = True
        
        # Check if game over
        if not self.valid_position(self.current_piece, self.current_piece.x, self.current_piece.y, self.current_piece.rotation):
            self.game_over = True

    def check_clear_lines(self):
        lines_to_clear = []
        for i in range(GRID_HEIGHT):
            if all(cell != 0 for cell in self.grid[i]):
                lines_to_clear.append(i)
        
        if not lines_to_clear:
            return
        
        # Update score
        lines_count = len(lines_to_clear)
        self.lines_cleared += lines_count
        self.score += [100, 300, 500, 800][min(lines_count - 1, 3)] * self.level
        
        # Update level
        self.level = self.lines_cleared // 10 + 1
        self.fall_speed = max(0.05, 0.5 - 0.05 * (self.level - 1))
        
        # Clear lines
        for line in reversed(lines_to_clear):
            del self.grid[line]
            self.grid.insert(0, [0 for _ in range(GRID_WIDTH)])

    def update_timer(self, dt):
        if not self.game_over and not self.paused:
            self.elapsed_time += dt

    def format_time(self, seconds):
        minutes = int(seconds) // 60
        seconds = int(seconds) % 60
        return f"{minutes:02d}:{seconds:02d}"

    def toggle_pause(self):
        self.paused = not self.paused

    def draw_grid(self):
        # Draw background
        screen.fill(BLACK)
        
        # Draw grid background and lines
        pygame.draw.rect(screen, BLACK, 
                       (GRID_OFFSET_X, GRID_OFFSET_Y, 
                        GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE))
        
        # Draw the background grid
        for i in range(GRID_HEIGHT + 1):
            # Horizontal lines
            pygame.draw.line(screen, DARK_GRAY, 
                           (GRID_OFFSET_X, GRID_OFFSET_Y + i * BLOCK_SIZE),
                           (GRID_OFFSET_X + GRID_WIDTH * BLOCK_SIZE, GRID_OFFSET_Y + i * BLOCK_SIZE))
        
        for j in range(GRID_WIDTH + 1):
            # Vertical lines
            pygame.draw.line(screen, DARK_GRAY, 
                           (GRID_OFFSET_X + j * BLOCK_SIZE, GRID_OFFSET_Y),
                           (GRID_OFFSET_X + j * BLOCK_SIZE, GRID_OFFSET_Y + GRID_HEIGHT * BLOCK_SIZE))
        
        # Draw grid border
        pygame.draw.rect(screen, WHITE, 
                        (GRID_OFFSET_X - 2, GRID_OFFSET_Y - 2, 
                        GRID_WIDTH * BLOCK_SIZE + 4, GRID_HEIGHT * BLOCK_SIZE + 4), 2)
        
        # Draw blocks in the grid
        for i in range(GRID_HEIGHT):
            for j in range(GRID_WIDTH):
                if self.grid[i][j] != 0:
                    color = COLORS[self.grid[i][j] - 1]
                    pygame.draw.rect(screen, color, 
                                   (GRID_OFFSET_X + j * BLOCK_SIZE, GRID_OFFSET_Y + i * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(screen, WHITE, 
                                   (GRID_OFFSET_X + j * BLOCK_SIZE, GRID_OFFSET_Y + i * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Draw current piece
        if not self.game_over and not self.paused:
            shape = self.current_piece.shape
            for _ in range(self.current_piece.rotation % 4):
                shape = self.current_piece.rotate_shape(shape)
            
            for i in range(len(shape)):
                for j in range(len(shape[0])):
                    if shape[i][j] == 0:
                        continue
                    
                    pygame.draw.rect(screen, self.current_piece.color, 
                                   (GRID_OFFSET_X + (self.current_piece.x + j) * BLOCK_SIZE, 
                                    GRID_OFFSET_Y + (self.current_piece.y + i) * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(screen, WHITE, 
                                   (GRID_OFFSET_X + (self.current_piece.x + j) * BLOCK_SIZE, 
                                    GRID_OFFSET_Y + (self.current_piece.y + i) * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Draw next piece preview
        next_label = font.render("Next:", True, WHITE)
        screen.blit(next_label, (SCREEN_WIDTH - 150, GRID_OFFSET_Y))
        
        shape = self.next_piece.shape
        for i in range(len(shape)):
            for j in range(len(shape[0])):
                if shape[i][j] == 0:
                    continue
                
                pygame.draw.rect(screen, self.next_piece.color, 
                               (SCREEN_WIDTH - 150 + j * BLOCK_SIZE, 
                                GRID_OFFSET_Y + 40 + i * BLOCK_SIZE, 
                                BLOCK_SIZE, BLOCK_SIZE))
                pygame.draw.rect(screen, WHITE, 
                               (SCREEN_WIDTH - 150 + j * BLOCK_SIZE, 
                                GRID_OFFSET_Y + 40 + i * BLOCK_SIZE, 
                                BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Draw hold piece
        hold_label = font.render("Hold:", True, WHITE)
        hold_status = font.render("(" + ("Available" if self.can_hold else "Used") + ")", True, 
                                WHITE if self.can_hold else GRAY)
        screen.blit(hold_label, (50, GRID_OFFSET_Y))
        screen.blit(hold_status, (50, GRID_OFFSET_Y + 40))
        
        if self.hold_piece:
            shape = self.hold_piece.shape
            for i in range(len(shape)):
                for j in range(len(shape[0])):
                    if shape[i][j] == 0:
                        continue
                    
                    color = self.hold_piece.color
                    if not self.can_hold:
                        # Darken the color to indicate it can't be used
                        color = tuple(max(c // 2, 0) for c in color)
                    
                    pygame.draw.rect(screen, color, 
                                   (50 + j * BLOCK_SIZE, 
                                    GRID_OFFSET_Y + 80 + i * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE))
                    pygame.draw.rect(screen, WHITE, 
                                   (50 + j * BLOCK_SIZE, 
                                    GRID_OFFSET_Y + 80 + i * BLOCK_SIZE, 
                                    BLOCK_SIZE, BLOCK_SIZE), 1)
        
        # Draw controls below the hold window
        controls_y = GRID_OFFSET_Y + 180
        controls = [
            "Controls:",
            "left/right arrow: Move",
            "up arrow: Rotate",
            "down arrow: Soft Drop",
            "Space: Hard Drop",
            "C: Hold",
            "P: Pause",
            "R: Restart"
        ]
        for i, text in enumerate(controls):
            label = small_font.render(text, True, WHITE)
            screen.blit(label, (50, controls_y + i * 20))
        
        # Draw score, level, and timer
        score_label = font.render(f"Score: {self.score}", True, WHITE)
        level_label = font.render(f"Level: {self.level}", True, WHITE)
        lines_label = font.render(f"Lines: {self.lines_cleared}", True, WHITE)
        time_label = font.render(f"Time: {self.format_time(self.elapsed_time)}", True, WHITE)
        
        score_y = GRID_OFFSET_Y + 340  # Position below controls
        screen.blit(score_label, (50, score_y))
        screen.blit(level_label, (50, score_y + 40))
        screen.blit(lines_label, (50, score_y + 80))
        screen.blit(time_label, (50, score_y + 120))  # Add timer display
        
        # Draw game over text
        if self.game_over:
            game_over_label = font.render("GAME OVER", True, RED)
            restart_label = font.render("Press R to restart", True, WHITE)
            final_time_label = font.render(f"Final Time: {self.format_time(self.elapsed_time)}", True, WHITE)
            
            screen.blit(game_over_label, (SCREEN_WIDTH // 2 - game_over_label.get_width() // 2, GRID_OFFSET_Y - 100))
            screen.blit(final_time_label, (SCREEN_WIDTH // 2 - final_time_label.get_width() // 2, GRID_OFFSET_Y - 60))
            screen.blit(restart_label, (SCREEN_WIDTH // 2 - restart_label.get_width() // 2, GRID_OFFSET_Y - 20))
        
        # Draw pause text
        if self.paused and not self.game_over:
            pause_overlay = pygame.Surface((GRID_WIDTH * BLOCK_SIZE, GRID_HEIGHT * BLOCK_SIZE))
            pause_overlay.set_alpha(128)  # Semi-transparent
            pause_overlay.fill(BLACK)
            screen.blit(pause_overlay, (GRID_OFFSET_X, GRID_OFFSET_Y))
            
            pause_label = font.render("PAUSED", True, WHITE)
            continue_label = font.render("Press P to continue", True, WHITE)
            
            screen.blit(pause_label, (SCREEN_WIDTH // 2 - pause_label.get_width() // 2, SCREEN_HEIGHT // 2 - 40))
            screen.blit(continue_label, (SCREEN_WIDTH // 2 - continue_label.get_width() // 2, SCREEN_HEIGHT // 2))

    def update(self, dt):
        if self.game_over or self.paused:
            return
        
        # Update the timer
        self.update_timer(dt)
        
        # Handle piece falling
        self.fall_timer += dt
        fall_step = self.fall_speed
        if self.fast_fall:
            fall_step = self.fall_speed / 10
        
        if self.fall_timer >= fall_step:
            self.fall_timer = 0
            if not self.move_piece(0, 1):
                self.place_piece()

# Main game loop
def main():
    game = TetrisGame()
    running = True
    dt = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.KEYDOWN:
                if game.game_over and event.key == pygame.K_r:
                    game.reset_game()
                
                if event.key == pygame.K_p and not game.game_over:
                    game.toggle_pause()
                
                if not game.game_over and not game.paused:
                    if event.key == pygame.K_LEFT:
                        game.move_piece(-1, 0)
                    elif event.key == pygame.K_RIGHT:
                        game.move_piece(1, 0)
                    elif event.key == pygame.K_DOWN:
                        game.fast_fall = True
                    elif event.key == pygame.K_UP:
                        game.rotate_piece()
                    elif event.key == pygame.K_SPACE:
                        game.drop_piece()
                    elif event.key == pygame.K_c:
                        game.hold()
                    elif event.key == pygame.K_r:
                        game.reset_game()
            
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_DOWN:
                    game.fast_fall = False
        
        game.update(dt)
        game.draw_grid()
        pygame.display.flip()
        dt = clock.tick(60) / 1000  # Convert to seconds
    
    pygame.quit()

if __name__ == "__main__":
    main()