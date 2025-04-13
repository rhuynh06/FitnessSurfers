from google import genai

client = genai.Client(api_key="")

def generate_direction_text(direction : str):
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents=f"You are a pt trainer, the runner you are training is going to hit a wall if they don't move to the {direction}. Tell them what to do, do not include any other text. Try to make it more than 3 words"
    )
    return response.text


def generate_game_over_text():
    response = client.models.generate_content(
        model="gemini-2.0-flash", contents='tell a joke to a player to cheer them. Only add text that will go directly to the player, be more creative, no phrase with pouch potato, do not make it obvious that you are cheering up the player'
    )
    return response.text

if __name__ == '__main__':
    #print(generate_direction_text('right'))
    print(generate_game_over_text())
