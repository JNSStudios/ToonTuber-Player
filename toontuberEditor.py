import pygame

# Initialize Pygame
pygame.init()

# Set up the window
WINDOW_WIDTH = 800
WINDOW_HEIGHT = 600
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
pygame.display.set_caption('ToonTuber Editor')

# Set up colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (200, 200, 200)

# Set up nodes
class Node:
    def __init__(self, x, y, width, height, label):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = BLACK
        self.selected = False
        self.label = label
        self.font = pygame.font.SysFont('Arial', 16)
        self.label_text = self.font.render(label, True, BLACK)
        self.label_pos = self.label_text.get_rect(center=self.rect.center)
    
    def draw(self):
        pygame.draw.rect(screen, self.color, self.rect)
        screen.blit(self.label_text, self.label_pos)
        if self.selected:
            pygame.draw.rect(screen, GRAY, self.rect, 3)
    
    def select(self):
        self.selected = True
    
    def deselect(self):
        self.selected = False
    
    def move(self, x, y):
        self.rect.center = (x, y)
        self.label_pos.center = self.rect.center
    
    def collides(self, x, y):
        return self.rect.collidepoint(x, y)

nodes = [Node(100, 100, 80, 40, 'Node 1'), Node(200, 200, 80, 40, 'Node 2')]


# Set up connections
class Connection:
    def __init__(self, node1, node2):
        self.node1 = node1
        self.node2 = node2
        self.color = BLACK
    
    def draw(self):
        pygame.draw.line(screen, self.color, self.node1.rect.center, self.node2.rect.center, 3)

connections = []

# Event loop
selected_node = None
dragging_node = False
click_time = 0
while True:
    for event in pygame.event.get():
        # Check if the window was closed
        if event.type == pygame.QUIT:
            # Quit Pygame
            pygame.quit()
            sys.exit()

        # Check if a key was pressed
        if event.type == pygame.KEYDOWN:
            # Delete the selected node or connection when the delete key is pressed
            if event.key == pygame.K_DELETE:
                if selected_node is not None:
                    nodes.remove(selected_node)
                    for connection in connections:
                        if connection.node1 == selected_node or connection.node2 == selected_node:
                            connections.remove(connection)
                elif selected_connection is not None:
                    connections.remove(selected_connection)

            # Create a new node when the space key is pressed
            elif event.key == pygame.K_SPACE:
                nodes.append(Node(*pygame.mouse.get_pos(), 80, 40, 'Node'))

        # Check if the mouse was clicked
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check if the left mouse button was clicked
            if event.button == 1:
                # Check if a node was clicked
                for node in nodes:
                    if node.collides(*event.pos):
                        selected_node = node
                        selected_connection = None
                        node.select()
                        click_time = pygame.time.get_ticks()
                        break

                # Check if a connection was clicked
                if selected_node is None:
                    for connection in connections:
                        if connection.collides(*event.pos):
                            if pygame.time.get_ticks() - click_time < 500:
                                # Double-click to break a connection
                                connections.remove(connection)
                                break
                            else:
                                selected_connection = connection
                                selected_node = None
                                break

            # Check if the right mouse button was clicked
            elif event.button == 3:
                # Check if a node was clicked
                for node in nodes:
                    if node.collides(*event.pos):
                        nodes.remove(node)
                        for connection in connections:
                            if connection.node1 == node or connection.node2 == node:
                                connections.remove(connection)
                        break

        # Check if the mouse was moved while dragging a node
        if event.type == pygame.MOUSEMOTION and dragging_node:
            selected_node.move(*event.pos)

        # Check if the mouse button was released after dragging a node
        if event.type == pygame.MOUSEBUTTONUP:
            dragging_node = False
            if selected_node is not None:
                selected_node.deselect()
                selected_node = None

    # Clear the screen
    screen.fill(WHITE)

    # Draw the nodes
    for node in nodes:
        node.draw()

    # Draw the connections
    for connection in connections:
        connection.draw()

    # Update the screen
    pygame.display.update()


#quit pygame 
pygame.quit()