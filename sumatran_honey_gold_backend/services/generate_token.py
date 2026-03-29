from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/youtube"]

# flow = InstalledAppFlow.from_client_secrets_file(
#     "secret_youtube.json",
#     SCOPES
# )

# creds = flow.run_local_server(port=8080)

# with open("youtube_token.json", "w") as token:
#     token.write(creds.to_json())

# print("Token generated!")

flow = InstalledAppFlow.from_client_secrets_file(
    "secret_youtube.json",
    SCOPES
)

auth_url, _ = flow.authorization_url(prompt='consent')

print("Go to this URL:")
print(auth_url)

code = input("Enter the authorization code: ")

flow.fetch_token(code=code)

creds = flow.credentials

with open("youtube_token.json", "w") as token:
    token.write(creds.to_json())

print("Token generated!")