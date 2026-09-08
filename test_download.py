import re

def extract_youtube_urls(text):
    pattern = r'https?://(?:www\.)?(?:youtube\.com/watch\?v=[\w-]{11}|youtu\.be/[\w-]{11})'
    return re.findall(pattern, text)

# Test
test_text = "https://www.youtube.com/watch?v=7wtfhZwyrcchttps://www.youtube.com/watch?v=kJQP7kiw5Fk"
urls = extract_youtube_urls(test_text)
print("URLs trouvées:", urls)

# Doit afficher:
# URLs trouvées: ['https://www.youtube.com/watch?v=7wtfhZwyrcc', 'https://www.youtube.com/watch?v=kJQP7kiw5Fk']
