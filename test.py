import pygame

# Initialize Pygame
pygame.init()

# Load the sprite sheet
sprite_sheet_path = 'dinoCharactersVersion1.1/sheets/DinoSprites - doux.png'  # Update with your path
sprite_sheet = pygame.image.load(sprite_sheet_path)

# Get the dimensions of the full sprite sheet
sheet_width, sheet_height = sprite_sheet.get_size()

# Number of frames horizontally
num_frames = 24

# Calculate the width and height of each frame
frame_width = sheet_width // num_frames
frame_height = sheet_height

print(f"Frame Width: {frame_width}")
print(f"Frame Height: {frame_height}")