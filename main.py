from discord.ext import commands
import discord
from datetime import datetime, timedelta
import random
import os
import json
import logging
import math
import re
from sanitize import sanitize


os.chdir(os.path.dirname(os.path.abspath(__file__)))
print("Current working directory:", os.getcwd())


#opens the specified json file and then return its contents
def openfile(file):
    with open(f"./data/{file}", "r") as f:
        data = json.load(f)
        f.close()
    return data 

#Save a users data without overriting existing data.
def save_user(user_id, data):
    users_data = openfile("users.json")
    users_data.setdefault("users", {}).setdefault(str(user_id), {}).update(data)
    with open("./data/users.json", "w") as f:
        json.dump(users_data, f, indent=4)
    f.close()

#Gets a user's data
def get_users(user_id=None):
    users = openfile("users.json").get("users", {})
    if user_id is None:
        return users
    return users.get(str(user_id), {})

#Dumps codes into the codes.json file
def save_codes(codes_data):
    existing_data = openfile("codes.json")
    existing_data.setdefault("codes", {}).update(codes_data.get("codes", {}))
    with open("./data/codes.json", "w") as f:
        json.dump(existing_data, f, indent=4)
    f.close()

#Generate a random string of specified chars and of a specified lengh and then saves it using the save codes function.
def generate_code(length=6):
    characters = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789"
    codes_data = openfile("codes.json")
    codes = codes_data.setdefault("codes", {})
    while True:
        code = ''.join(random.choice(characters) for _ in range(length))
        if code not in codes:
            codes[code] = {"used": False}
            save_codes(codes_data)
            return code

#Code that can generate codes on a loop
def generate_codes(amount=1, length=6):
    codes = []
    for _ in range(amount):
        code = generate_code(length)
        codes.append(code)
    return codes

#Returns a list of all non used codes.
def get_valid_codes():
    codes = openfile("codes.json").get("codes", {})
    return [code for code, data in codes.items() if not data.get("used", False)]

#Returns the status for that code: None, False or True
def check_code(code, used=True):
    codes_data = openfile("codes.json")
    code_data = codes_data.get("codes", {}).get(code)
    if code_data is None:
        return None
    if code_data.get("used", False):
        return False
    if used:
        code_data["used"] = True
        save_codes(codes_data)
    return True

#Delete any code that has not been used
def delete_unused_codes():
    codes_data = openfile("codes.json")
    codes_data["codes"] = {
        code: data
        for code, data in codes_data.get("codes", {}).items()
        if data.get("used", False)
    }
    save_codes(codes_data)

#Sets the start time for the bot (used for the /status command)
start_time = datetime.now()
#Loads the config json
config = openfile("config.json")
#Extract and load the token from the config
token = config["token"]
#Sets up a logging handler
handler = logging.FileHandler(filename='./data/discord.log', encoding='utf-8', mode='w')

print("Starting discord bot...")

#Configure the intents for the bot
intents = discord.Intents.default()
intents.message_content = True
intents.members = True

#Syncs all the commands to all the specified serveurs in the config file
class CgBot(commands.Bot):
    async def setup_hook(self):
        for server_id in config["serverids"]:
            guild = discord.Object(id=int(server_id))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        await self.tree.sync()
        print("Commands synced!")

bot = CgBot(command_prefix="!", intents=intents)

#A function to send a specified message to a specified channel
async def sendbot(message,channel="botstuff"):
    channel = bot.get_channel(int(config["channelids"][channel]))
    if channel is None:
        print(f"Channel {channel} was not found.")
    else:
        try:
            await channel.send(message)
        except discord.Forbidden:
            print(f"The bot cannot send messages in the {channel} channel.")


#Triggers when the bot boots up
@bot.event
async def on_ready():
    await bot.change_presence(status=discord.Status.online, activity=discord.Activity(type=discord.ActivityType.watching, name=config["botstatus"]))
    await sendbot(f"Le bot est en ligne.")
    print(f"Bot is ready! Bot is {bot.user.name}")


#Locks down certain channels
@bot.event
async def on_message(message):
    if message.author.bot:
        return

    if message.channel.id == int(config["channelids"]["verify"]):
        try:
            await message.delete()
            await message.channel.send(
                f"{message.author.mention}, vous ne pouvez pas envoyer de message dans ce channel. Utilisez la commande `/code`.",
                delete_after=5,
            )
        except discord.Forbidden:
            print("The bot cannot delete or send messages in the verify channel.")
        return

    await bot.process_commands(message)


#Checks the bot uptime and version
@bot.tree.command(name="status", description="Permet de voir la version et le temp de fonctionnement du bot")
async def status_command(interaction: discord.Interaction):
    try:
        uptime = datetime.now() - start_time
        uptime_str = str(timedelta(seconds=int(uptime.total_seconds())))
        version = config["version"]
        await interaction.response.send_message(f"Le bot est en ligne!\nUptime: {uptime_str}\nVersion: {version}", ephemeral=True)
    except Exception as e:
        print(f"Error in status_command: {e}")
        await interaction.response.send_message("Une erreur est survenue lors de l'éxécution du code", ephemeral=True)


#Reload the config.json file
@bot.tree.command(name="reload", description="Recharger la configuration du bot.")
async def reload_command(interaction: discord.Interaction):
    global config
    if str(interaction.user.id) in config["trustedids"]:
        config = openfile("config.json")
        await interaction.response.send_message("La configuration du bot a été rechargée.", ephemeral=True)
    else:
        await interaction.response.send_message("La configuration du bot ne peut être rechargée que par les administrateurs.", ephemeral=True)


#Just replies back with hello
@bot.tree.command(name="salut", description="Dit salut!")
async def hello_command(interaction: discord.Interaction):
    await interaction.response.send_message(f"Salut {interaction.user.mention}", ephemeral=True)


#Returns the sqrt root of a provided number
@bot.tree.command(name="sqrt", description="Calcule la racine carrée d'un nombre.")
async def sqrt_command(interaction: discord.Interaction, nombre: float):
    nombre = sanitize(nombre)
    result = math.sqrt(nombre)
    await interaction.response.send_message(f"La racine carrée de {nombre} est {result}.", ephemeral=True)


#Returns the result to a math expression using the eval() function. 
#Security might need to be improved on this part since it is very prone to attacks
@bot.tree.command(name="eval", description="Évalue une expression mathématique.")
async def eval_command(interaction: discord.Interaction, expression: str):
    expression = sanitize(expression)
    try:
        result = eval(expression)
        await interaction.response.send_message(f"Le résultat de {expression} est {result}.", ephemeral=True)
    except Exception as e:
        await interaction.response.send_message(f"Erreur lors de l'évaluation de {expression}", ephemeral=True)


#Returns a user profile in a fancy embeded
@bot.tree.command(name="profile", description="Retourne le profil d'un membre.")
async def profile_command(interaction: discord.Interaction, member: discord.Member):
    embed = discord.Embed(title=f"Profile de {member}", color=discord.Color.green())
    embed.set_thumbnail(url=member.avatar.url if member.avatar else None)
    embed.add_field(name="ID", value=member.id, inline=False)
    embed.add_field(name="Nom: ", value=get_users(member.id).get('name', 'inconnu'), inline=False)
    embed.add_field(name="Nom afiché", value=member.display_name, inline=False)
    embed.add_field(name="Création du compte", value=member.created_at.strftime('%Y-%m-%d %H:%M:%S'), inline=False)
    embed.add_field(name="Rejoint le serveur", value=member.joined_at.strftime('%Y-%m-%d %H:%M:%S') if member.joined_at else "N/A", inline=False)
    embed.add_field(name="Roles", value=", ".join([role.name for role in member.roles if role.name != "@everyone"]) or "No roles", inline=False)
    await interaction.response.send_message(embed=embed, ephemeral=True)


#Allows a user to change his name
@bot.tree.command(name="name", description="Changer votre nom de membre vérifié.")
async def name_command(interaction: discord.Interaction, name: str):
    name = sanitize(name)
    if name == "*":
        await interaction.response.send_message(f"Votre nom est: {get_users(interaction.user.id).get('name', 'inconnu')}.", ephemeral=True)
    else:
        await interaction.response.send_message(f"Votre nom a été changé de {get_users(interaction.user.id).get('name', 'inconnu')} à {name}.", ephemeral=True)
        save_user(interaction.user.id, {"name": name})


#Checks if a code is correct, and if it is, it grants the member role
@bot.tree.command(name="code", description="Vérifier un code de vérification pour obtenir le rôle de membre.")
async def code_command(interaction: discord.Interaction, code: str, name: str):
    name = sanitize(name)
    code = sanitize(code)
    if interaction.channel.id != config["channelids"]["verify"]:
            await interaction.response.send_message("❌Cette commande ne peut être utilisée que le channel dédié.", ephemeral=True)
            return
    code_status = check_code(code)
    if code_status is True:
        await interaction.response.send_message("Code correct ✅! Vous avez été vérifié.", ephemeral=True)
        await sendbot(f"✅User {interaction.user.mention} has been verified with the code ({code}).")
        await sendbot(f"Bienvenue {interaction.user.mention} ({name})!", channel="welcome")
        await interaction.user.add_roles(discord.Object(id=config["roleids"]["verified"]))
        save_user(interaction.user.id, {"name": name, "codeused": code})
    else:
        await interaction.response.send_message("Code incorrect ❌. Veuillez réessayer.", ephemeral=True)
        await sendbot(f"❌User {interaction.user.mention} entered a incorrect code ({code}).")


#Admin commands for managing codes sutch as generating new ones, seeing the actives codes, and deleteing unused codes.
@bot.tree.command(name="codeadmin", description="Commandes d'admin pour gérer les codes de vérification.")
async def codeadmin_command(interaction: discord.Interaction, action: str, amount: int = 1):
    if interaction.channel.id == config["channelids"]["codesadmin"] and str(interaction.user.id) in config["trustedids"]:
        
        if action == "gen":
            codes = generate_codes(amount)
            await interaction.response.send_message(f"Codes générés: {', '.join(codes)}")
        elif action == "list":
            valid_codes = get_valid_codes()
            await interaction.response.send_message(f"Codes valides: {', '.join(valid_codes)}")
        elif action == "delete_unused":
            delete_unused_codes()
            await interaction.response.send_message("Les codes inutilisés ont été supprimés.")
        else:
            await interaction.response.send_message("Action invalide. Veuillez utiliser 'gen', 'list' ou 'delete_unused'.", ephemeral=True)
    else:
        await interaction.response.send_message("❌Cette commande ne peut être utilisée que le channel dédié et par des personnes autorisées.", ephemeral=True)
        await sendbot(f"❌User {interaction.user.mention} tried to use the codeadmin command in the wrong channel or without permission.")
        return


#A less refined version of the codeadmin command. May also be used to test other commands beffor implementing them.
@bot.tree.command(name="debug", description="Debug commands (disabled by default).")
async def debug_command(interaction: discord.Interaction, command: str):
    if config["debug"]:
        if command == "delete_unused_codes":
            delete_unused_codes()
            await interaction.response.send_message("Unused codes have been deleted.", ephemeral=True)
        elif command == "check_codes":
            valid_codes = get_valid_codes()
            await interaction.response.send_message(f"Valid codes: {', '.join(valid_codes)}", ephemeral=True)
        elif command == "generate_codes":
            codes = generate_codes()
            await interaction.response.send_message(f"Generated codes: {', '.join(codes)}", ephemeral=True)
    else:
        await interaction.response.send_message("Debug mode is disabled.", ephemeral=True)


print("Running bot...")

#Starts the bot with the token and the log handler
bot.run(token, log_handler=handler, log_level=logging.INFO)