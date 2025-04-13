from google import genai

client = genai.Client(api_key="") # Replace with your actual API key

def generate_game_over_text():
    response = client.models.generate_content(
        model="gemini-2.0-flash", 
        contents='encourage player to try again (subway surfers game), at most 20 words'
    )
    return response.text

if __name__ == '__main__':
    print(generate_game_over_text())