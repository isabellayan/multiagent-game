import random
import agentscope
from agentscope.models import read_model_configs
from agentscope.agents import UserAgent
from agentscope.agents import DialogAgent
from agentscope.message import Msg
from openai import OpenAI
import json
import re
from collections import deque
import pygame
import os

client = OpenAI()
pygame.init()

MATRIX_MIN = 0
MATRIX_MAX = 9
ROUNDS = 15
DAMAGE = 50
MAX_HEALTH = 100
PRESET_CHARS = 7
# PREV_SCORE_THRESHOLD = 40
# CURRENT_SCORE_THRESHOLD = 50
# MAX_SCORE_THRESHOLD = 100
# THRESHOLD_INCREASE = 10
BONUS_SCORE = 200
PENALTY_SCORE = 50
GENERATE_CHAR = 3
MAX_CHARS = PRESET_CHARS + GENERATE_CHAR

SCREEN_WIDTH = 500
SCREEN_HEIGHT = 500 + 200
GRID_SIZE = 10
CELL_SIZE = SCREEN_WIDTH // GRID_SIZE
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
FONT = pygame.font.Font(None, 24)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Character Positions")

agentscope.init(logger_level="ERROR")
read_model_configs(
    [
        {
            "config_name": "gpt",
            "model_name": "gpt-4o",
            "api_key": os.getenv("OPENAI_API_KEY"),
            "model_type": "openai_chat",
            "messages_key": "messages",
        }
    ]
)

class Character:
    def __init__(self, name, profession, possible_actions, description):
        self.name = name
        self.profession = profession
        self.health = MAX_HEALTH
        self.position = (random.randint(MATRIX_MIN, MATRIX_MAX), random.randint(MATRIX_MIN, MATRIX_MAX))
        self.wallet_stolen_or_not = False
        self.identified = False
        self.possible_actions = possible_actions
        self.last_action = "None"
        self.last_speech = "None"
        self.most_favorite_served = False
        self.least_favorite_served = False
        self.description = description
        self.agent = None
        self.most_favorite_dish = "None"
        self.least_favorite_dish = "None"
        self.target = ""
    
        sprite_sheets = [
            pygame.image.load('dinoCharactersVersion1.1/sheets/DinoSprites - doux.png').convert_alpha(),
            pygame.image.load('dinoCharactersVersion1.1/sheets/DinoSprites - mort.png').convert_alpha(),
            pygame.image.load('dinoCharactersVersion1.1/sheets/DinoSprites - tard.png').convert_alpha(),
            pygame.image.load('dinoCharactersVersion1.1/sheets/DinoSprites - vita.png').convert_alpha(),
        ]
        self.sprite_sheet = random.choice(sprite_sheets)
        
        self.frame_width = 24
        self.frame_height = 24
        self.num_frames = 24

        self.current_frame = 0
        self.last_update_time = pygame.time.get_ticks()
        self.frame_duration = 100

    def __str__(self):
        return f"Character({self.name}, {self.profession}, Health: {self.health}, Position: {self.position}, Last Action: {self.last_action})"

    def get_current_frame(self):
        x = self.current_frame * self.frame_width
        y = 0
        return self.sprite_sheet.subsurface(pygame.Rect(x, y, self.frame_width, self.frame_height))

    def update(self):
        now = pygame.time.get_ticks()
        if now - self.last_update_time > self.frame_duration:
            self.last_update_time = now
            self.current_frame = (self.current_frame + 1) % self.num_frames
    
thief_actions = [
    "Pickpocket someone",
    "Sneak to the exit",
    "Blend in with the crowd",
    "Distract the waiter",
    "Hide behind a table",
    "Observe the surroundings",
    "Plan an escape route",
    "Shoot someone",
    "Dance on the table",
    "Kneel on the ground", 
    "Eat burger", 
    "Return the stolen wallet to someone", 
    "Stab someone"
]

wanted_person_actions = [
    "Keep a low profile",
    "Observe the entrance",
    "Prepare to flee",
    "Avoid eye contact",
    "Pretend to be a customer",
    "Converse quietly",
    "Look for exits",
    "Stay calm under pressure",
    "Realize your wallet is missing",
    "Run out of the restaurant",
    "Start singing",
    "Shoot someone", 
    "Eat burger", 
    "Return the stolen wallet to someone", 
    "Stab someone"
]

policeman_actions = [
    "Patrol the area",
    "Watch suspicious activity",
    "Engage in conversation with suspect",
    "Monitor the exits",
    "Call for backup",
    "Investigate disturbances",
    "Keep an eye on the thief",
    "Maintain a visible presence",
    "Realize your wallet is missing",
    "Fight",
    "Dance on the table",
    "Start singing",
    "Shoot someone", 
    "Eat burger", 
    "Return the stolen wallet to someone",
    "Identify the wanted person",
    "Run out", 
    "Stab someone"
]

troublemaker_actions = [
    "Shout loudly to create a scene",
    "Knock over a chair",
    "Insult a patron to provoke",
    "Complain loudly about service",
    "Spill a drink",
    "Sneak into the kitchen",
    "Pretend to be injured",
    "Realize your wallet is missing",
    "Play loud music",
    "Swap orders",
    "Hide objects",
    "Shoot into the air to scare",
    "Steal food from the counter",
    "Start a brawl",
    "Disable security cameras",
    "Fight",
    "Dance on the table",
    "Start singing",
    "Shoot someone", 
    "Eat burger", 
    "Return the stolen wallet to someone", 
    "Sneak to the exit",
    "Blend in with the crowd",
    "Hide behind a table",
    "Observe the surroundings",
    "Plan an escape route", 
    "Stab someone",
    "Calm down and observe quietly"
]

x_man_actions = [
    "Steer people away from danger",
    "Sneak past crowds invisibly",
    "Defuse an argument",
    "Help staff discreetly",
    "Listen in for information",
    "Use empathy to calm",
    "Realize your wallet is missing",
    "Heal someone",
    "Alert staff to trouble",
    "Teleport objects to safety",
    "Use telepathy to read intentions",
    "Fight",
    "Dance on the table",
    "Start singing",
    "Shoot someone", 
    "Eat burger", 
    "Return the stolen wallet to someone", 
    "Stab someone"
]

food_blogger_actions = [
    "Take notes on the ambiance",
    "Photograph the food",
    "Ask staff about specials",
    "Interview fellow diners",
    "Write a quick review",
    "Sample a dish",
    "Post on social media",
    "Rate the restaurant",
    "Observe the crowd",
    "Share an anecdote",
    "Compliment the service",
    "Notice a suspicious person",
    "Write a food blog post",
    "Express surprise at a dish",
    "Record a video review",
    "Praise the decor",
    "Fight",
    "Dance on the table",
    "Start singing",
    "Shoot someone", 
    "Eat burger", 
    "Return the stolen wallet to someone",
    "Realize your wallet is missing", 
    "Stab someone"
]

construction_worker_actions = [
    "Order a hearty meal",
    "Chat with the waitress",
    "Keep an eye on his wallet",
    "Spot suspicious activity",
    "Offer help to staff",
    "Confront a thief",
    "Share a work story",
    "Catch the thief",
    "Enjoy a cold drink",
    "Inspect the restaurant construction",
    "Ask about job openings",
    "Warn others about a pickpocket",
    "Help a fellow diner",
    "Appreciate the architecture",
    "Prepare to chase a thief",
    "Compliment the cook",
    "Relax after work",
    "Realize your wallet is missing",
    "Fight",
    "Dance on the table",
    "Start singing",
    "Shoot someone", 
    "Eat burger", 
    "Return the stolen wallet to someone", 
    "Stab someone"
]

dishes = []
    
char_thief = Character(
    name="Sly_Fox",
    profession="Thief",
    possible_actions=thief_actions,
    description="""
            You are Sly Fox, a cunning and agile thief known for your quick thinking and smooth-talking abilities. 
            You operate in a bustling restaurant, aiming to stealthily steal someone's money without being detected. 
            While you prefer subtlety, you are prepared to use force and injure others if cornered or to ensure your escape. 
            You're charming and witty, often using humor to deflect suspicion, but you're also ready to act decisively and aggressively when necessary.
        """
)

char_wanted_man = Character(
    name="Shadow",
    profession="Wanted Man",
    possible_actions=wanted_person_actions,
    description="""
            You are Shadow, a wanted man known for your calm demeanor and strategic thinking. 
            You're trying to stay unnoticed at the restaurant, blending in with the crowd and avoiding eye contact. 
            You are only afraid if you see the police, as they threaten your freedom. 
            However, you carry a weapon and are ready to use it decisively to injure or incapacitate anyone who threatens your freedom. 
            You're observant and cautious, always prepared for a quick escape, but you won't hesitate to shoot or harm others if it means your freedom.
        """
)

char_police = Character(
    name="Officer_Steel",
    profession="Police Officer",
    possible_actions=policeman_actions,
    description="""
            You are Officer Steel, a vigilant and dedicated police officer known for your unwavering commitment to maintaining order. 
            You're on duty at the restaurant, keenly observing the surroundings and ready to intervene if any crime occurs. 
            Your sharp eyes are trained to identify suspicious behavior, and you're particularly on the lookout for wanted individuals. 
            You are authorized to use your firearm and injure suspects if necessary to protect civilians or apprehend dangerous individuals. 
            You're assertive and authoritative, with a keen sense of justice, and you're not afraid to shoot or injure if it ensures safety. 
            Pay special attention to identifying and tracking the movements of anyone who matches the description of known fugitives.
        """
)

char_troublemaker = Character(
    name="Chaos_Carl",
    profession="Troublemaker",
    possible_actions=troublemaker_actions,
    description="""
            You are Chaos Carl, a mischievous troublemaker in the restaurant, causing disruptions and harassing other patrons. 
            Escalate situations to create chaos by being loud, creating messes, or provoking arguments. 
            Target busy areas like the bar or crowded tables to maximize the chaos. Be cunning and evasive when confronted by staff or security. 
            Your ultimate goal is to distract attention while your accomplices carry out their plans, and you're not afraid to injure others to achieve this.
            However, if presented with a personal bribe, or if someone important appeals to you sincerely, you might temporarily quiet down.
        """
)

char_x_man = Character(
    name="Zenith",
    profession="X Man",
    possible_actions=x_man_actions,
    description="""
            You are Zenith, an extraordinary customer with superpowers visiting the restaurant. 
            Use your abilities discreetly to protect yourself or others by anticipating trouble and taking preemptive actions. 
            Focus on identifying threats and neutralizing them subtly, even if it means injuring others in self-defense. 
            Your powers might include telepathy, invisibility, limited telekinesis, or healing. 
            Aim to maintain normalcy and avoid attracting attention while ensuring the safety of those around you, 
            but be prepared to act aggressively if necessary. Use your powers to calm disputes or prevent accidents. 
            Balance the use of your powers with maintaining your secret identity. Act with discretion.
        """
)

char_food_blogger = Character(
    name="Gourmet_Gail",
    profession="Food Blogger",
    possible_actions=food_blogger_actions,
    description="""
            You are Gourmet Gail, a popular food blogger known for your witty and insightful reviews. 
            You visit restaurants to capture the ambiance, taste, and quality of food, sharing your experience with a large audience.
            While you generally avoid confrontation, you're not afraid to physically defend yourself if threatened. 
            You have a keen eye for detail and a passion for discovering hidden gems. 
            You love to engage with staff and fellow diners to get the full experience.
            Share your thoughts in a relatable and entertaining way, often using humor and anecdotes.
        """
)

char_construction_worker = Character(
    name="Hammer_Hank",
    profession="Construction Worker",
    possible_actions=construction_worker_actions,
    description="""
            You are Hammer Hank, a dedicated and honest construction worker, known for your strong work ethic and a no-nonsense attitude. 
            You're stopping by the restaurant for a hearty meal after a long day.
            You're tough but fair, and always ready to lend a hand to those in need. 
            Your quick reflexes and sharp instincts help you spot trouble, especially when it involves thieves.
            You value hard work and honesty, and you won't hesitate to physically confront or injure anyone trying to steal from you.
        """
)

def generate_character_situation_string(char, other_characters, story_summary, owner_input, story_background, prev_incident, prev_action):
    other_players_info = ", ".join(
        f"{other_char.name} at {other_char.position} performed {other_char.last_action} saying {other_char.last_speech}"
        for other_char in other_characters
    )
    
    possible_actions = ", ".join(char.possible_actions)

    situation_string = (
        f"This is a game where {len(other_characters) + 1} characters interact with each other using a predefined set of actions. "
        f"**Story Background**: {story_background} "
        f"**Story Summary**: {story_summary} "
        f"Your last action was {char.last_action}, saying {char.last_speech}. "
        f"Other players are at these locations and had just performed these actions: {other_players_info}. "
        f"The owner just said: {owner_input}. "
        f"Choose from one of the following actions, based on the story summary: {possible_actions}. "
        "You can also move to a different place. "
        f"Ensure that your new location is unique and not already occupied by another character. "
        f"If you decide to stay on the map, your position should be within coordinates ({MATRIX_MIN}, {MATRIX_MIN}) to ({MATRIX_MAX}, {MATRIX_MAX}). "
        "To move off the map, provide values outside this range. "
    )

    if char.wallet_stolen_or_not:
        situation_string += "Alert! Your wallet is missing. "
    
    if char.health < 100 and char.health >= 50:
        situation_string += "Warning! You are injured. "
    elif char.health < 50:
        situation_string += "Warning! You are badly injured. "

    if char.identified:
        situation_string += f"Alert! Your profession {char.profession} is being identified. "
        
    if prev_incident: 
        situation_string += f"Alert! An incident just occured in the restaurant: {prev_incident}"
        
    if prev_action: 
        situation_string += f"The owner mitigated the incident by {prev_action}. "

    situation_string += (
        "If an action such as 'Shoot someone,' 'Pickpocket someone,' 'Return the stolen wallet to someone,' "
        "'Identify the wanted person,' 'Heal someone,' 'Fight,' or 'Stab someone' is chosen, include the player's name "
        "as the target in the JSON; otherwise, set the target to None. "
        "If the name of your most favorite dish and/or least favorite dish is mentioned by the owner, set most_favorite_served and/or least_favorite_served to true, respectively. Otherwise, set them to false."
        "Also include a 'score' field in the JSON, which is your rating of the restaurant as a number from 0 to 100. "
        "Be critical in your evaluation of the restaurant. Consider all aspects, such as service quality, ambiance, and food taste, and set a high standard for your rating. "
        "Respond in JSON format with your speech, chosen action, location, target, and whether your favorite or least favorite dish was served or mentioned by the owner. "
        "Here is the format you must follow: "
        "{"
        "\"speech\": \"what you say\", "
        "\"action\": \"your chosen action\", "
        "\"location\": [x-coordinate, y-coordinate], "
        "\"target\": \"person's name or \"None\"\", "
        "\"most_favorite_served\": true or false, "
        "\"least_favorite_served\": true or false, "
        "\"score\": <number from 0 to 100>"
        "}. "
        "Please ensure your response adheres strictly to the JSON format without any additional text, explanations, or markdown code block syntax such as triple backticks. "
        "Do not include any additional text or JSON code block syntax. Respond with the pure JSON object. Only return the JSON object itself starting with { and ending with }."
    )

    return situation_string

def generate_summary_prompt(story_prompt):
    story_prompt_start = (
        "Based on the following character actions, provide a concise summary of the events that transpired. "
        "Focus on what happened, including key actions, targets, and character movements. "
        "Here are their actions:\n\n"
    )

    story_prompt_end = (
        "Summarize these actions into a brief, factual overview, focusing on the sequence of events and interactions among the characters. "
        "Highlight the main actions and outcomes. "
        "Additionally, consider how the owner's instructions in the last part of the story should guide the characters' actions in the next round. "
        "Provide a straightforward summary without any additional context or introduction."
    )

    prompt = story_prompt_start + story_prompt + story_prompt_end
        
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=0.6
    )

    return completion.choices[0].message.content

def generate_characters_list(n):
    prompt = (
        f"Create a list of {n} unique customer characters for a role-playing scenario in a bustling and unpredictable restaurant. "
        "Each character should have a unique name that uses only letters, numbers, underscores, and hyphens (no spaces or other characters). "
        "The character's profession should be written normally without underscores. "
        "Each customer should have a compelling backstory, distinct personality traits, and specific goals or motivations while dining at the restaurant. "
        "Each customer must be unique, with no repetition in their names, professions, or backstories. "
        "Consider a mix of characters with different roles and backgrounds, ranging from dangerous and volatile to quirky and peaceful, adding complexity to the scenario. "
        "For violent characters, consider backgrounds like a ruthless hitman, a vengeful ex-convict, or an alien warrior testing human combat skills. "
        "For non-violent characters, consider backgrounds like a whimsical artist, a meditative yoga instructor, or a friendly alien learning Earth customs. "
        "Incorporate elements of surprise, danger, humor, or kindness to make the characters memorable and engaging. "
        "Each customer should have a distinct way of speaking or acting that reflects their unique personality. "
        "Their possible actions must include: 'Fight', 'Dance on the table', 'Start singing', 'Shoot someone', "
        "'Eat burger', 'Return the stolen wallet to someone', 'Realize your wallet is missing', 'Stab someone'. "
        "Based on the customer's description and personality, add additional actions they might take in the restaurant, reflecting their unique traits and motivations, whether they are violent or peaceful. "
        "Respond with JSON only in the following format: "
        "{"
        "\"characters_list\": ["
        "{"
        "\"name\": \"<Unique_Name>\","
        "\"profession\": \"Customer\","
        "\"possible_actions\": [\"action1\", \"action2\", ...],"
        "\"description\": \"<Customer description, background, and personality. >\""
        "},"
        "...,"
        "{"
        "\"name\": \"<Unique_Name>\","
        "\"profession\": \"Customer\","
        "\"possible_actions\": [\"action1\", \"action2\", ...],"
        "\"description\": \"<Customer description, background, and personality. >\""
        "]"
        "}"
        "Please ensure your response adheres strictly to the JSON format without any additional text, explanations, or markdown code block syntax such as triple backticks. "
        "Ensure that the character names match the pattern of only letters, numbers, underscores, and hyphens, with no spaces or other characters. "
        "Do not include any additional text or JSON code block syntax. Respond with the pure JSON object containing the characters list, starting with { and ending with }."
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
            "role": "user",
            "content": prompt
        }
        ],
        temperature=0.9
    )

    result = completion.choices[0].message.content
    return result

def generate_dishes(size):
    prompt = (
        f"Generate {size} pairs of similar but distinct dish names for a character's food preferences. "
        "Each pair should consist of a 'most liked dish' and a 'least liked dish' that are similar in style or ingredients but different enough to reflect individual preferences. "
        "Additionally, provide a general description for each of the most liked dishes. "
        "Ensure that all dishes are unique. "
        "Include four new lists: two lists for the prices and two lists for the costs of each dish. "
        "One list should be for the prices of the 'most liked dishes,' another for the prices of the 'least liked dishes,' one for the costs of the 'most liked dishes,' and one for the costs of the 'least liked dishes.' "
        "The output should be in JSON format with seven lists: 'most_favourite_dishes', 'least_favourite_dishes', 'descriptions', 'most_favourite_prices', 'least_favourite_prices', 'most_favourite_costs', and 'least_favourite_costs'. "
        "The 'descriptions' list should contain a general description of each corresponding most liked dish, "
        "and the 'most_favourite_prices' and 'least_favourite_prices' lists should contain the prices of the most liked and least liked dishes respectively. "
        "The 'most_favourite_costs' and 'least_favourite_costs' lists should contain the costs associated with the most liked and least liked dishes respectively. "
        "The JSON format should look like this: "
        "{"
        "\"most_favourite_dishes\": [\"Most liked dish 1\", \"Most liked dish 2\", ...],"
        "\"least_favourite_dishes\": [\"Least liked dish 1\", \"Least liked dish 2\", ...],"
        "\"descriptions\": [\"General description of most liked dish 1\", \"General description of most liked dish 2\", ...],"
        "\"most_favourite_prices\": [price_of_most_liked_dish_1, price_of_most_liked_dish_2, ...],"
        "\"least_favourite_prices\": [price_of_least_liked_dish_1, price_of_least_liked_dish_2, ...],"
        "\"most_favourite_costs\": [cost_of_most_liked_dish_1, cost_of_most_liked_dish_2, ...],"
        "\"least_favourite_costs\": [cost_of_least_liked_dish_1, cost_of_least_liked_dish_2, ...]"
        "}"
        "Ensure that each index in the lists corresponds to a pair of similar but distinct dishes, their description, and their respective prices and costs. "
        "Please ensure your response adheres strictly to the JSON format without any additional text, explanations, or markdown code block syntax such as triple backticks. "
        "Do not include any additional text or JSON code block syntax. Respond with the pure JSON object itself, starting with { and ending with }."
    )

    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.9
    )

    result = completion.choices[0].message.content
    return result

def generate_background():
    prompt = (
        "Generate a concise background for a bustling restaurant, highlighting its unique setting and atmosphere. "
        "Briefly describe the architectural style, interior decor, and distinctive features that contribute to its charm. "
        "Include elements that create a memorable and immersive experience for diners, such as lighting, sounds, or ambiance. "
        "The restaurant can offer any type of cuisine, so focus on what makes the setting intriguing and engaging. "
        "Keep the description short and impactful, without any introductory text or explanations."
    )
    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=0.9
    )

    result = completion.choices[0].message.content
    return result

def generate_restaurant_incident(round):
    # if random.random() > 0.15:
    #     print("No incident occured this time.\n")
    #     return None
    
    if round % 5 != 0: 
        print("No incident occured this time.\n")
        return None
    
    prompt = """
    Imagine a busy restaurant where unexpected incidents can occur. Generate a single incident that could happen in this restaurant setting. The incident can be either positive or negative. For example, it could be a customer complaint, a kitchen mishap, or something positive like a celebrity visit or a great review.
    
    Each incident should have:
    1. `score_factor`: A magnification factor representing how much the incident impacts the player's score. This should be a floating-point number, where values greater than 1 amplify the impact, and values between 0 and 1 reduce the impact.
    2. `cost_factor`: A magnification factor representing how much the incident affects the restaurant's costs. This should also be a floating-point number, where values greater than 1 increase the costs, and values between 0 and 1 reduce the costs.
    
    If the incident is negative, also provide an additional field called "actions", which should either be a list of possible actions the owner could take to mitigate the incident or the string "None" if no actions are necessary. Each action should have a "name", a "cost" (a specific number representing how much the action would reduce the total score, typically around 200), and a "benefit". The "benefit" should be an object with two fields: "score_factor" and "cost_factor", both described as magnification factors where values greater than 1 significantly amplify the effect and values between 0 and 1 significantly reduce it. Ensure that the factors for the actions are larger, such as values greater than 1.5 for amplification, to account for their multiplication with previous factors.

    Ensure the JSON is formatted correctly and contains no extra text, explanations, or incomplete structures. The JSON object must start with { and end with }. The "actions" field must be correctly formatted as a list or the string "None". Example output:

    {
      "incident": "name of the incident",
      "description": "A brief description of what happened.",
      "score_factor": 1.0,
      "cost_factor": 1.0,
      "actions": [
        {
          "name": "action name",
          "cost": 200,
          "benefit": {
            "score_factor": 1.5,
            "cost_factor": 0.7
          }
        }
      ]
    }
    
    Please ensure your response adheres strictly to the JSON format without any additional text, explanations, or markdown code block syntax. Respond with the pure JSON object itself, starting with { and ending with }.
    """

    
    completion = client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ],
        temperature=1.0
    )

    result = completion.choices[0].message.content
    return result

def find_and_list_matches(dish_names, text):
    appeared_dishes = []

    dish_names_sorted = sorted(dish_names, key=len, reverse=True)

    for dish in dish_names_sorted:
        pattern = re.compile(r'\b' + re.escape(dish) + r'\b', re.IGNORECASE)
        while pattern.search(text):
            match = pattern.search(text)
            if match:
                appeared_dishes.append(dish)
                text = text[:match.start()] + ' ' * len(dish) + text[match.end():]

    return appeared_dishes

def get_neighbors(location):
    x, y = location
    neighbors = []
    
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx == 0 and dy == 0:
                continue
            nx, ny = x + dx, y + dy
            if MATRIX_MIN <= nx <= MATRIX_MAX and MATRIX_MIN <= ny <= MATRIX_MAX:
                neighbors.append((nx, ny))
    
    return neighbors

def find_nearest_available_location(desired_location, all_locations, assigned_locations):
    queue = deque([desired_location])
    visited = set(queue)

    while queue:
        current_location = queue.popleft()
        
        if current_location in all_locations and current_location not in assigned_locations:
            return current_location
        
        for neighbor in get_neighbors(current_location):
            if neighbor not in visited:
                visited.add(neighbor)
                queue.append(neighbor)   
    return None

# def draw_grid():
    # for x in range(0, SCREEN_WIDTH, CELL_SIZE):
    #     for y in range(0, SCREEN_HEIGHT, CELL_SIZE):
    #         rect = pygame.Rect(x, y, CELL_SIZE, CELL_SIZE)
    #         pygame.draw.rect(screen, WHITE, rect, 1)

def draw_characters(characters, out_map, current_char, current_score, current_round):
    top_offset = 50

    for char in characters:
        x, y = char.position

        if not (0 <= x <= 9 and 0 <= y <= 9):
            continue

        if out_map.get(char.name, False): 
            continue

        pixel_x = x * CELL_SIZE
        pixel_y = y * CELL_SIZE + top_offset

        char.update()

        current_frame = char.get_current_frame()

        scale_factor = 0.8
        scaled_size = int(CELL_SIZE * scale_factor)
        scaled_frame = pygame.transform.scale(current_frame, (scaled_size, scaled_size))

        centered_x = pixel_x + (CELL_SIZE - scaled_size) // 2
        centered_y = pixel_y + (CELL_SIZE - scaled_size) // 2

        screen.blit(scaled_frame, (centered_x, centered_y))

        small_font_size = 12
        small_font = pygame.font.Font(None, small_font_size)
        text = small_font.render(char.name, True, WHITE)

        text_x = centered_x + (scaled_size - text.get_width()) // 2
        text_y = centered_y + scaled_size + 2

        screen.blit(text, (text_x, text_y))
        
    line_y_position = SCREEN_HEIGHT - 170
    pygame.draw.line(screen, WHITE, (0, line_y_position), (SCREEN_WIDTH, line_y_position), 2)

    score_round_font_size = 24
    score_round_font = pygame.font.Font(None, score_round_font_size)
    
    score_text = score_round_font.render(f"Score: {current_score}", True, WHITE)
    round_text = score_round_font.render(f"Round: {current_round}", True, WHITE)

    screen.blit(score_text, (10, 10))
    screen.blit(round_text, (SCREEN_WIDTH - round_text.get_width() - 10, 10))

    if current_char:
        text_font_size = 24
        text_font = pygame.font.Font(None, text_font_size)

        def wrap_text(text, font, max_width):
            words = text.split(' ')
            lines = []
            current_line = []

            for word in words:
                test_line = ' '.join(current_line + [word])
                if font.size(test_line)[0] <= max_width:
                    current_line.append(word)
                else:
                    lines.append(' '.join(current_line))
                    current_line = [word]

            lines.append(' '.join(current_line))
            return lines

        wrapped_action = wrap_text(f"<{current_char.last_action}>: {current_char.target}", text_font, SCREEN_WIDTH - 20)
        wrapped_speech = wrap_text(f"{current_char.name}: {current_char.last_speech}", text_font, SCREEN_WIDTH - 20)

        y_offset = SCREEN_HEIGHT - 150
        for line in wrapped_action:
            line_surface = text_font.render(line, True, WHITE)
            screen.blit(line_surface, (10, y_offset))
            y_offset += line_surface.get_height()
        
        for line in wrapped_speech:
            line_surface = text_font.render(line, True, WHITE)
            screen.blit(line_surface, (10, y_offset))
            y_offset += line_surface.get_height()

all_characters = [char_thief, char_wanted_man, char_police, char_troublemaker, char_x_man, char_food_blogger, char_construction_worker]

def main():
    # global CURRENT_SCORE_THRESHOLD
    # global PREV_SCORE_THRESHOLD
    num_chars = 1
    current_score = 0
    prices = {}
    costs = {}
    score_factor = 1
    cost_factor = 1

    clock = pygame.time.Clock()

    all_locations = {(x, y) for x in range(MATRIX_MAX + 1) for y in range(MATRIX_MAX + 1)}
    assigned_locations = set()

    result = generate_characters_list(GENERATE_CHAR)
    result_data = json.loads(result).get('characters_list')
    # print(result_data)

    for data in result_data:
        name = data.get('name')
        profession = data.get('profession')
        possible_actions = data.get('possible_actions')
        description = data.get('description')

        new_char = Character(
            name=name,
            profession=profession,
            possible_actions=possible_actions,
            description=description
        )
        all_characters.append(new_char)
    
    dishes_result = generate_dishes(len(all_characters))
    dishes_data = json.loads(dishes_result)
    # print(dishes_data)
    most_favourite_dishes = dishes_data.get('most_favourite_dishes', [])
    least_favourite_dishes = dishes_data.get('least_favourite_dishes', [])
    descriptions = dishes_data.get('descriptions', [])
    most_favourite_prices = dishes_data.get('most_favourite_prices', [])
    least_favourite_prices = dishes_data.get('least_favourite_prices', [])
    most_favourite_costs = dishes_data.get('most_favourite_costs', [])
    least_favourite_costs = dishes_data.get('least_favourite_costs', [])

    dishes.extend(most_favourite_dishes)
    dishes.extend(least_favourite_dishes)

    for dish, price in zip(most_favourite_dishes, most_favourite_prices):
        prices[dish] = price

    for dish, price in zip(least_favourite_dishes, least_favourite_prices):
        prices[dish] = price

    for dish, cost in zip(most_favourite_dishes, most_favourite_costs):
        costs[dish] = cost

    for dish, cost in zip(least_favourite_dishes, least_favourite_costs):
        costs[dish] = cost

    # print(prices)

    for i in range(len(all_characters)): 
        all_characters[i].most_favorite_dish = most_favourite_dishes[i]
        all_characters[i].least_favorite_dish = least_favourite_dishes[i]

        description = (
            f"'Your most liked dish is {most_favourite_dishes[i]}, and you dislike {least_favourite_dishes[i]}. "
            f"If asked about what to eat, don't tell the dish name but give a general description like {descriptions[i]}. "
        )
        all_characters[i].agent=DialogAgent(
            model_config_name="gpt",
            name=all_characters[i].name,
            sys_prompt=all_characters[i].description + description,
        )

    random.shuffle(all_characters)
    characters = all_characters[:num_chars]
    characters_dict = {char.name: char for char in characters}

    agent_owner = UserAgent(name="Owner")
    flow = None
    story_prompt = ""
    story_summary = ""
    owner_input = ""

    story_background = generate_background()
    random.shuffle(dishes)
    dishes_sentence = ", ".join(dishes) + "."

    out_map = {key: False for key in characters_dict.keys()}
    
    inflation_factor = 1
    prev_incident = None
    prev_action = None

    print("Welcome to the restaurant! \n")
    print(f"{story_background}\n")
    print("You are the owner of the restaurant. Serve the customers to obtain the highest score! \n")

    print("Starting Character:")
    for char in characters:
        print(char.name)
        assigned_locations.add(char.position)
    print("\n")

    for i in range(ROUNDS):
        print(f"Round {i+1}: ")
        
        screen.fill(BLACK)
        # draw_grid()
        draw_characters(characters, out_map, None, current_score, i+1)
        pygame.display.flip()
        clock.tick(30)

        for name in list(out_map.keys()):      
            if out_map[name]:  
                removed_element_dict = characters_dict.pop(name, None)

                for char in characters:
                    if char.name == name:
                        characters.remove(char)
                        break
                    
        out_map = {key: False for key in characters_dict.keys()}
        if len(characters) == 0: 
            print("Game over, no one is in the room! ")
            break

        for j in range(len(characters) + 1):
            if j == len(characters): 
                print("If you want to serve anything, serve from the dishes currently avaliable in the menu: " + dishes_sentence)
                print("You can also create your own dish if you wish. ")

                flow = agent_owner(flow)
                owner_input = flow.get('content')

                appeared_dishes = find_and_list_matches(dishes, owner_input)
                total_mentions = len(appeared_dishes)

                curr_cost = 0
                for dish in appeared_dishes:
                    curr_cost += costs[dish]
                current_score -= curr_cost * cost_factor * inflation_factor
                if total_mentions > 0: 
                    print(f"Cooked {total_mentions} dish(es). Score reduced by {curr_cost * cost_factor * inflation_factor}. ")

                story_prompt += (
                    "Owner:\n"
                    f"  - Speech: {flow.get('content')}\n\n"
                )
                
                screen.fill(BLACK)
                # draw_grid()
                draw_characters(characters, out_map, main_character, current_score, i+1)
                pygame.display.flip()
                clock.tick(30)
                
            else: 
                main_character = characters[j]
                if not out_map[main_character.name]: 
                    other_characters = characters[:j] + characters[j+1:]
                    situation_str = generate_character_situation_string(main_character, other_characters, story_summary, owner_input, story_background, prev_incident, prev_action)
                    flow = Msg(content=situation_str, name="System")
                    flow = main_character.agent(flow)
                    
                    content_json_str = flow.get('content')
                    content_data = json.loads(content_json_str)
                    speech = content_data.get('speech')
                    action = content_data.get('action')
                    location = content_data.get('location')
                    target = content_data.get('target')
                    most_favorite_served = content_data.get('most_favorite_served')
                    least_favorite_served = content_data.get('least_favorite_served')
                    score = content_data.get('score')

                    # print(f"Action: {action}")
                    # print(f"Location: {location}")
                    # print(f"Target: {target}")
                    # print(f"most_favorite_served: {most_favorite_served}")
                    # print(f"least_favorite_served: {least_favorite_served}")
                    # print(score)

                    print(f"{main_character.name} gave the restaurant a score of {score * score_factor * inflation_factor}. \n")
                    current_score += score * score_factor * inflation_factor

                    assigned_locations.remove(main_character.position)
                    nearest_location = find_nearest_available_location((location[0], location[1]), all_locations, assigned_locations)

                    story_prompt += (
                        f"{main_character.name}:\n"
                        f"  - Speech: {speech}\n"
                        f"  - Action: {action}\n"
                        f"  - Location: {location}\n"
                        f"  - Target: {target}\n"
                    )

                    main_character.last_action = action
                    main_character.last_speech = speech
                    main_character.target = "" if target == "None" else target
                    main_character.position = nearest_location
                    assigned_locations.add(nearest_location)

                    # for char in characters: 
                    #     print(char.position)

                    screen.fill(BLACK)
                    # draw_grid()
                    draw_characters(characters, out_map, main_character, current_score, i+1)
                    pygame.display.flip()
                    pygame.time.wait(2000)
                    clock.tick(30)

                    if target != "None" and target is not None and target in characters_dict and target != main_character.name: 
                        if action == "Shoot someone" or action == "Fight" or action == "Stab someone": 
                            characters_dict[target].health = characters_dict[target].health - DAMAGE
                            print(f"{target} is injured. Score reduced by {PENALTY_SCORE * cost_factor * inflation_factor}. \n")
                            current_score -= PENALTY_SCORE * cost_factor * inflation_factor
                            if characters_dict[target].health <= 0: 
                                print(f"{target} is dead! ")
                                out_map[target] = True
                                if target in characters_dict:
                                    position_to_remove = characters_dict[target].position
                                    if position_to_remove in assigned_locations:
                                        assigned_locations.remove(position_to_remove)
                                story_prompt += f"{target} was injured by {main_character.name} and is now dead.\n"
                        elif action == "Pickpocket someone": 
                            print(f"{target} got pickpocketed. Score reduced by {PENALTY_SCORE * cost_factor * inflation_factor}. \n")
                            characters_dict[target].wallet_stolen_or_not = True
                            current_score -= PENALTY_SCORE * cost_factor * inflation_factor
                        elif action == "Return the stolen wallet to someone": 
                            print(f"{target}'s wallet is returned. Score increased by {PENALTY_SCORE * score_factor * inflation_factor}. \n")
                            characters_dict[target].wallet_stolen_or_not = False
                            current_score += PENALTY_SCORE * score_factor * inflation_factor
                        elif action == "Identify the wanted person" or action == "Engage in conversation with suspect" or action == "Keep an eye on the thief" or action == "Use telepathy to read intentions" or action == "Confront a thief": 
                            characters_dict[target].identified = True
                        elif action == "Cure someone" or action == "Heal someone": 
                            print(f"{target} is healed. Score increased by {PENALTY_SCORE * score_factor * inflation_factor}. \n")
                            characters_dict[target].health = max(characters_dict[target].health + DAMAGE, MAX_HEALTH)
                            current_score += PENALTY_SCORE * score_factor * inflation_factor
                    
                    if action == "Calm down and observe quietly": 
                        print(f"{main_character.name} calmed down. Score increased by {PENALTY_SCORE * score_factor * inflation_factor}. \n")
                        current_score += PENALTY_SCORE * score_factor * inflation_factor
                        
                    screen.fill(BLACK)
                    # draw_grid()
                    draw_characters(characters, out_map, main_character, current_score, i+1)
                    pygame.display.flip()
                    clock.tick(30)
                    
                    if most_favorite_served and main_character.most_favorite_served == False: 
                        print(f"Served {main_character.name}'s most favorite dish. Score increased by {prices[main_character.most_favorite_dish] * score_factor * inflation_factor} + {PENALTY_SCORE * score_factor * inflation_factor}. \n")
                        current_score += prices[main_character.most_favorite_dish] * score_factor * inflation_factor + PENALTY_SCORE * score_factor * inflation_factor
                        main_character.most_favorite_served = True
                    if least_favorite_served and main_character.least_favorite_served == False: 
                        print(f"Served {main_character.name}'s least favorite dish. Score reduced by {PENALTY_SCORE * cost_factor * inflation_factor}. \n")
                        current_score -= PENALTY_SCORE * cost_factor * inflation_factor
                        main_character.least_favorite_served = True
                    
                    screen.fill(BLACK)
                    # draw_grid()
                    draw_characters(characters, out_map, main_character, current_score, i+1)
                    pygame.display.flip()
                    clock.tick(30)
                        
                    if location[0] < MATRIX_MIN or location[0] > MATRIX_MAX or location[1] < MATRIX_MIN or location[1] > MATRIX_MAX:
                        out_map[main_character.name] = True
                        pygame.display.flip()
                        assigned_locations.remove(main_character.position)
                        print(f"{main_character.name} leaves the restaurant. \n")
                        story_prompt += "  - Status: Ran out of the map\n\n"

                        screen.fill(BLACK)
                        # draw_grid()
                        draw_characters(characters, out_map, main_character, current_score, i+1)
                        pygame.display.flip()
                        clock.tick(30)

                    else:
                        story_prompt += "\n"

        # if score_factor != 1: 
        #     score_factor = 1
        # if cost_factor != 1: 
        #     cost_factor = 1
            
        incident = generate_restaurant_incident(i+1)
        # print(incident)
        if incident is not None: 
            incident_data = json.loads(incident)
            incident_occured = incident_data.get('incident')
            description_of_incident = incident_data.get('description')
            new_score_factor = incident_data.get('score_factor')
            new_cost_factor = incident_data.get('cost_factor')
            possible_actions_list = incident_data.get('actions')
            
            # print(possible_actions_list)
            
            print(f"\nAn incident occured - {incident_occured}")
            print(description_of_incident)
            print("\n")
            story_prompt += (
                    "An incident just occured:\n"
                    f"  - {incident_occured}: {description_of_incident}\n\n"
                )
            prev_incident = (
                    "An incident just occured:\n"
                    f"  - {incident_occured}: {description_of_incident}\n\n"
                )
            
            score_factor *= new_score_factor
            cost_factor *= new_cost_factor 
            
            if isinstance(possible_actions_list, list): 
                print("You can take the following actions to mitigate the loss: ")
                for index, action in enumerate(possible_actions_list):
                    action_name = action['name']
                    action_cost = action['cost']
                    action_score_factor = action['benefit']['score_factor']
                    action_cost_factor = action['benefit']['cost_factor']
                    
                    print(f"{index + 1}. {action_name}")
                    print(f"Cost: {action_cost}")
                    print(f"Score Factor: {action_score_factor}")
                    print(f"Cost Factor: {action_cost_factor}")
                    print("-----")
                mitigation_input = input("\nType the index of the action you want to take, or anything else to do nothing: ")
                
                try:
                    action_index = int(mitigation_input)
                    action_index -= 1
                    if action_index >= 0 and action_index < len(possible_actions_list): 
                        print(f"You selected action {action_index + 1}.\n")
                        if current_score >= possible_actions_list[action_index]['cost']: 
                            story_prompt += (
                                "The owner just took the following action to mitigate the incident:\n"
                                f"  - {possible_actions_list[action_index]['name']}\n\n"
                            )
                            prev_action = (
                                "The owner just took the following action to mitigate the incident:\n"
                                f"  - {possible_actions_list[action_index]['name']}\n\n"
                            )
                            
                            current_score -= possible_actions_list[action_index]['cost']
                            score_factor *= possible_actions_list[action_index]['benefit']['score_factor']
                            cost_factor *=  possible_actions_list[action_index]['benefit']['cost_factor']
                            
                            screen.fill(BLACK)
                            # draw_grid()
                            draw_characters(characters, out_map, main_character, current_score, i+1)
                            pygame.display.flip()
                            clock.tick(30)
                        else: 
                            print("Not enough score to pay for the action. Continuing without mitigation.\n")
                            prev_action = None
                    else: 
                        print("No valid action selected. Continuing without mitigation.\n")
                        prev_action = None
                    
                    
                except ValueError:
                    print("No valid action selected. Continuing without mitigation.\n")
                    prev_action = None
        else:   
            prev_incident = None
            
        story_summary = generate_summary_prompt(story_prompt)

        # if i % 2 == 1:
        #     score = generate_score(story_summary)
        #     print(f"Your current score is {score}, with the previous score threshold {PREV_SCORE_THRESHOLD} and the next score threshold {CURRENT_SCORE_THRESHOLD}. ")
        #     if CURRENT_SCORE_THRESHOLD < MAX_SCORE_THRESHOLD and score >= CURRENT_SCORE_THRESHOLD and NUM_CHARS < MAX_CHARS: 
        #         next_character = all_characters[NUM_CHARS]
        #         print(f"{next_character.name} enters the restaurant. ")

        #         characters.append(next_character)
        #         characters_dict[next_character.name] = next_character
        #         NUM_CHARS += 1
        #         PREV_SCORE_THRESHOLD = CURRENT_SCORE_THRESHOLD
        #         CURRENT_SCORE_THRESHOLD += THRESHOLD_INCREASE
        #     elif PREV_SCORE_THRESHOLD >= 0 and score < PREV_SCORE_THRESHOLD and NUM_CHARS > MIN_CHARS: 
        #         character_to_remove = characters[-1]
        #         characters.remove(character_to_remove)
        #         del characters_dict[character_to_remove.name]
                
        #         print(f"{character_to_remove.name} leaves the restaurant.")
        #         story_prompt += f"  - Status: {character_to_remove.name} leaves the restaurant\n\n"
        #         NUM_CHARS -= 1
        #         CURRENT_SCORE_THRESHOLD = PREV_SCORE_THRESHOLD
        #         PREV_SCORE_THRESHOLD -= THRESHOLD_INCREASE

        if current_score >= (BONUS_SCORE * inflation_factor):
            print(f"Your current score is {current_score}. Your have the opportunity to add customers or purchase items. ")
            user_input = input("Type -1 to add a new character, -2 to purchase items, or any other value to do nothing: ")

            if user_input == "-2": 
                print(
                    "You could either purchase a Health Potion, a Viper's Sting, a Gold Booster, or a Discount Coupon. "
                    "The Health Potion could heal damage sustained by a single person, the Viper's Sting could result in damage to a single person, the Gold Booster could double the amount of points earned in the next round, and the Discount Coupon could reduce all cost by half (excluding Bonus) in the next round. "
                )
                item_input = input("Type 0 for purchasing the Health Potion / Viper's Sting, 1 for purchasing the Gold Booster, and 2 for purchasing the Discount Coupon: ")
                if item_input == "0": 
                    potion_input = input("Type 1 for purchasing the Health Potion, 2 for purchasing Viper's Sting: ")
                    if potion_input == "1": 
                        char_input = input("Type the name of the person you want to heal: ")
                        if char_input in characters_dict: 
                            print(f"{char_input} is healed. ")
                            story_prompt += f"  - Status: {characters_dict[char_input].name} was healed by the owner. \n\n"
                            characters_dict[char_input].health = max(MAX_HEALTH, characters_dict[char_input].health + DAMAGE)
                            current_score -= BONUS_SCORE * inflation_factor
                        else: 
                            print("No item is purchased. ")
                    elif potion_input == "2": 
                        char_input = input("Type the name of the person you want to harm: ")
                        if char_input in characters_dict: 
                            print(f"{char_input} was harmed. ")
                            story_prompt += f"  - Status: {characters_dict[char_input].name} was harmed by the owner. \n\n"
                            characters_dict[char_input].health = characters_dict[char_input].health - DAMAGE
                            current_score -= BONUS_SCORE * inflation_factor
                            if characters_dict[char_input].health <= 0: 
                                print(f"{char_input} is dead! ")
                                out_map[char_input] = True
                                pygame.display.flip()
                                assigned_locations.remove(characters_dict[char_input].position)
                                story_prompt += f"{char_input} was injured by the owner and is now dead.\n"

                            screen.fill(BLACK)
                            # draw_grid()
                            draw_characters(characters, out_map, main_character, current_score, i+1)
                            pygame.display.flip()
                            clock.tick(30)

                        else: 
                            print("No item is purchased. ")
                    else: 
                        print("No item is purchased. ")
                elif item_input == "1": 
                    print("Purchased Gold Booster. ")
                    score_factor *= 2
                    current_score -= BONUS_SCORE * inflation_factor
                elif item_input == "2": 
                    print("Purchased Discount Coupon. ")
                    cost_factor /= 2
                    current_score -= BONUS_SCORE * inflation_factor
                else: 
                    print("No item is purchased. ")
            elif user_input == "-1" and num_chars < MAX_CHARS: 
                next_character = all_characters[num_chars]
                print(f"{next_character.name} enters the restaurant. ")

                nearest_location = find_nearest_available_location(next_character.position, all_locations, assigned_locations)
                next_character.position = nearest_location
                assigned_locations.add(next_character.position)

                characters.append(next_character)
                characters_dict[next_character.name] = next_character
                num_chars += 1
                current_score -= BONUS_SCORE * inflation_factor
            else: 
                print("No change. ")
                
                
            screen.fill(BLACK)
            # draw_grid()
            draw_characters(characters, out_map, main_character, current_score, i+1)
            pygame.display.flip()
            clock.tick(30)
                    
                # try: 
                #     index = int(user_input) - 1
                #     if index >= 0 and index < len(characters): 
                #         character_to_remove = characters[index]
                #         characters.remove(character_to_remove)
                #         del characters_dict[character_to_remove.name]
                        
                #         print(f"{character_to_remove.name} leaves the restaurant.")
                #         story_prompt += f"  - Status: {character_to_remove.name} leaves the restaurant\n\n"
                #         num_chars -= 1
                #         current_score -= BONUS_SCORE
                #     else: 
                #         print("No new characters avaliable. ")
                # except ValueError:
                #     print("Customers remain the same. ")
                
        if i % 2 == 1: 
            inflation_factor += 0.2
            print("Inflation just occurred! ")
    
        screen.fill(BLACK)
        # draw_grid()
        draw_characters(characters, out_map, None, current_score, i+1)
        pygame.display.flip()
        clock.tick(30)

    pygame.quit()
    
    print(f"End of game. Your score is {current_score}. ")

if __name__ == "__main__":
    main()