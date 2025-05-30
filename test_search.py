from youtube_utils import search_users

# Test searching for a user with public email
print("Searching for 'egg' with respect_privacy=True:")
results = search_users("egg", respect_privacy=True)
print(f"Found {len(results)} results:")
for user in results:
    print(f"Username: {user.get('username')}, Email: {user.get('email')}, Public Email: {user.get('public_email')}")

print("\nSearching for 'influencer' with respect_privacy=True:")
results = search_users("influencer", respect_privacy=True)
print(f"Found {len(results)} results:")
for user in results:
    print(f"Username: {user.get('username')}, Email: {user.get('email')}, Public Email: {user.get('public_email')}")

print("\nSearching for all users regardless of privacy:")
results = search_users("", respect_privacy=False)
print(f"Found {len(results)} results in total (all users)")