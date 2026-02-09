from google import genai

client = genai.Client()

response = client.models.generate_content(
    model="gemini-2.0-flash",
    contents="Hello Vertex AI"
)

print(response.text)
