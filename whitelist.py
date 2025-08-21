import discord
from discord import option
from discord.ext import commands
import json
import aiohttp

# Variables
BOT_TOKEN = <bot token here>
WHITELIST_FILE = <path to whitelist file here>
GUILD_ID = <discord guild id here>
ROLE_ID = <discord role id here>

bot = discord.Bot(debug_guilds=[GUILD_ID])

async def get_uuid(gameType: str, username: str):
    """
    Fetch the UUID and username for a given Minecraft account.
    Args:
        gameType (str): The type of Minecraft account, either "java" or "bedrock".
        username (str): The username or gamertag of the Minecraft account.
    Returns:
        tuple: A tuple containing the UUID and username.
            For Java accounts, it returns (uuid, username).
            For Bedrock accounts, it returns (java_uuid, java_name) if linked,
            otherwise (floodgateuid, .gamertag).
            Returns (None, None) if the request fails.
    """
    apiVal = "username" if gameType == "java" else "gamertag"
    url = f"https://mcprofile.io/api/v1/{gameType}/{apiVal}/{username}"

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
            else:
                return (None, None)

    if gameType == "bedrock":
        if data["linked"] == True:
            return (data["java_uuid"], data["java_name"]) # Linked Bedrock Account
        else:
            return (data["floodgateuid"], f".{data['gamertag']}") # Unlinked Bedrock Account
    else:
        return (data["uuid"], data["username"]) # Java Account

async def add_to_whitelist(uuid, username):
    """
    Asynchronously adds a user to the whitelist.
    This function reads the current whitelist from a JSON file, checks if the user
    is already whitelisted based on their UUID, and if not, adds the user to the
    whitelist and writes the updated list back to the file.
    Args:
        uuid (str): The UUID of the user to be added to the whitelist.
        username (str): The username of the user to be added to the whitelist.
    Returns:
        bool: True if the user was successfully added to the whitelist, False if the
        user was already in the whitelist.
    Raises:
        IOError: If there is an error reading from or writing to the whitelist file.
    """
    try:
        with open(WHITELIST_FILE, "r") as f:
            whitelist = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        whitelist = []

    # Check if user is already whitelisted
    if any(entry["uuid"] == uuid for entry in whitelist):
        return False

    # Add new entry
    whitelist.append({"uuid": uuid, "name": username})

    with open(WHITELIST_FILE, "w") as f:
        json.dump(whitelist, f, indent=4)

    return True

@bot.slash_command(name="whitelist", description="Whitelist a Minecraft user")
@commands.has_role(ROLE_ID)
@option("gametype", description="Java or Bedrock Edition", choices=["Java", "Bedrock"])
@option("username", description="Minecraft Username/Xbox Gamertag", required=True)
async def whitelist(ctx: discord.ApplicationCommand, gametype: str, username: str):
    """
    Adds a user to the whitelist for a specified game type.
    Parameters:
        ctx (discord.ApplicationCommand): The context of the command invocation.
        gametype (str): The type of game, either "java" or "bedrock".
        username (str): The username of the player to be whitelisted.
    Returns:
        None
    """
    await ctx.response.defer()

    gametype = gametype.lower()
    if gametype not in ["java", "bedrock"]:
        await ctx.respond("Invalid type. Please choose either Java or Bedrock.", ephemeral=True)
        return

    uuid, name = await get_uuid(gametype, username)
    if not uuid:
        await ctx.respond(f"Could not retrieve UUID for {username}.", ephemeral=True)
        return

    success = await add_to_whitelist(uuid, name)
    if success:
        await ctx.respond(f"Successfully whitelisted {name} (UUID: {uuid})!")
    else:
        await ctx.respond(f"{name} is already whitelisted!", ephemeral=True)

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')


bot.run(BOT_TOKEN)
