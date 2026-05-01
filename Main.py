import discord, json, datetime, traceback, random, requests, os, io, re, time, asyncio
from discord import app_commands
from discord.app_commands import Choice
from discord.ext import commands
from discord.utils import utcnow
from datetime import timedelta, datetime, UTC
from dotenv import load_dotenv
from rgb2hex import  rgb2hex

## [--------------Colours--------------]
embed_blue = discord.Color.from_rgb(58, 195, 249)

with open("server_data.json", "r") as f:
    server_data = json.load(f)
    print(server_data)

intents = discord.Intents.default()
intents.message_content = True
intents.members = True

bot = commands.Bot(command_prefix=".", intents=intents, help_command=None)
tree = bot.tree


load_dotenv()
TOKEN = os.getenv("TOKEN")

async def Log(title, embed_content, colour):
    log = discord.Embed(title=title, description=embed_content[:4000], color=colour)
    if len(embed_content) > 4000:
        print('longgggggggggggggggggggggggggggggggggg')
    channel = int(server_data['Data']['logs'])
    await bot.get_channel(channel).send(embed=log)

async def sus(member: discord.Member):
    user = await member.guild._state._get_client().fetch_user(member.id)
    username = user.name

    points = 0
    flags = []

    if len(re.findall(r"\d", username)) >= 4 or re.fullmatch(r"[a-zA-Z0-9]{8,}", username) or re.search(r"(.)\1{3,}", username):
        points += 1
        flags.append("Robotic username")

    if user.avatar is None:
        points += 1
        flags.append("Blank avatar")

    if member.display_name == member.name:
        points += 1
        flags.append("No display name")

    if (discord.utils.utcnow() - user.created_at) < timedelta(days=60):
        points += 1
        flags.append("Recently created")

    if not flags:
        flags = ['None']
    return points, flags

async def generate_captcha(captcha, difficulty):
    response = requests.post("https://api.opencaptcha.io/captcha", json=
    {
        "text": str(captcha),
        "difficulty": int(difficulty),
        "width": 800,
        "height": 200, }, headers={"accept": "application/json"})

    return response.status_code, discord.File(io.BytesIO(response.content))

@bot.command()
async def check(ctx, member: discord.Member = None):
    member = member or ctx.author
    points, flags = await sus(member)
    pending_message = await ctx.message.reply('Reviewing member... 🔎')
    review_embed = discord.Embed(title='Member overview',
                                 description=f'Total points: ``{points}/4``' 
                                             f'\nFlags:\n``{"\n".join(flags)}``',
                                 color=embed_blue)
    await pending_message.edit(embed=review_embed, content='Review complete! ✅')

@tree.command(name="check", description="View a member's points")
@commands.has_permissions(moderate_members=True)
@app_commands.describe(member='Member to review')
async def review_member(interaction: discord.Interaction,member: discord.Member):
    points, flags = await sus(member)
    await interaction.response.send_message('Reviewing member... 🔎', ephemeral=True)
    review_embed = discord.Embed(title='Member overview',
                                 description=f'Total points: ``{points}/4``' 
                                             f'\nFlags:\n``{"\n".join(flags)}``',
                                 color=embed_blue)
    await interaction.edit_original_response(embed=review_embed, content='Review complete! ✅')


@tree.command(name='set-up', description='Set up your server')
@app_commands.describe(verification_channel='Verification channel')
@app_commands.describe(difficulty='Verification difficulty')
@app_commands.choices(difficulty=[
    Choice(name='Minimal', value='minimal'),
    Choice(name='Basic', value='basic'),
    Choice(name='Moderate', value='moderate'),
    Choice(name='Challenging', value='challenging'),
    Choice(name='Dynamic', value='dynamic'),])
@app_commands.describe(unverified_role="Unverified role")
@app_commands.describe(verified_role='Verified role')
@app_commands.describe(logs='Logs Channel')
async def set_up(interaction: discord.Interaction, verification_channel: discord.TextChannel, difficulty: str,
                 unverified_role: discord.Role, verified_role: discord.Role, logs: discord.TextChannel):
    whitelist = [interaction.guild.owner_id, 1200795455131500545]
    if not interaction.user.id in whitelist:
        await interaction.response.send_message('You do not have permission to do that.', ephemeral=True)
        return
    overview_embed = discord.Embed(title='Set-up overview',
                                   description=f'Verification channel: {verification_channel.mention}'
                                            f'\nDifficulty: ``{difficulty}``'
                                            f'\nUnverified role: {unverified_role.mention}'
                                            f'\nVerified role: {verified_role.mention}'
                                            f'\nLogs channel: {logs.mention}',
                                   color=discord.Color.blue()
                                   )
    await Log('Set-up overview', f'Verification channel: {verification_channel.mention}'
                                            f'\nDifficulty: ``{difficulty}``'
                                            f'\nUnverified role: {unverified_role.mention}'
                                            f'\nVerified role: {verified_role.mention}'
                                            f'\nLogs channel: {logs.mention}'
                                            f'\nSet-up by: {interaction.user.mention}', embed_blue)
    await interaction.response.send_message(embed=overview_embed, ephemeral=True)

    server_data['Data']['logs'] = str(logs.id)
    server_data['Data']['diff'] = str(difficulty)
    server_data['Data']['unver'] = str(unverified_role.id)
    server_data['Data']['ver'] = str(verified_role.id)

    with open("server_data.json", "w") as f:
        json.dump(server_data, f, indent=4)



@tree.command(name="mute", description="Timeout/mute a member")
@app_commands.describe(member="Member")
@app_commands.describe(reason="Reason")
@app_commands.describe(minutes="Minutes")
@app_commands.describe(hours="Hours")
@app_commands.describe(days="Days")
async def mute(interaction: discord.Interaction, member: discord.Member, reason: str, minutes: int, hours: int, days: int):

    if not (interaction.user.guild_permissions.moderate_members or interaction.user.guild_permissions.mute_members):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return

    await interaction.response.send_message(
        f'Muting: {member.mention}\nReason: {reason}\nDuration: {days} days, {hours} hours, {minutes} minutes', ephemeral=True)

    duration = timedelta(minutes=minutes, hours=hours, days=days)
    try:
        await member.timeout(utcnow() + duration, reason=reason)

        await Log(
            'Muted member',
            f'\n Member: {member.mention}'
            f'\n Muted by: {interaction.user.mention}'
            f'\nReason: {reason}'
            f'\nDuration: {days}d {hours}h {minutes}m',
            discord.Color.yellow()
        )
        await interaction.edit_original_response(
            content=f'Muting: {member.mention}\nReason: {reason}\nDuration: {days} days, {hours} hours, {minutes} minutes')
    except discord.Forbidden:
        await interaction.edit_original_response(content="***I*** don't have permission to unmute this user. "
                                                         "\nPlease contact the server owner or administrator.",)
    except Exception as e:
        await interaction.edit_original_response(content=f"Error: {e}",)


@tree.command(name="unmute", description="Remove timeout/unmute a member")
@app_commands.describe(member="Member")
@app_commands.describe(reason="Reason")
async def unmute(interaction: discord.Interaction, member: discord.Member, reason: str):
    if not (interaction.user.guild_permissions.moderate_members or interaction.user.guild_permissions.mute_members):
        await interaction.response.send_message("You are not authorized to use this command.", ephemeral=True)
        return
    await interaction.response.send_message(content=f'Unmuting: {member.mention}\nReason: {reason}', ephemeral=True)

    try:
        await member.timeout(None, reason=reason)

        await interaction.edit_original_response(
            content=f'Unmuted: {member.mention}\nReason: {reason}')

        await Log('Unmuted member',
                  f'Member: {member.mention}'
                  f'\nReason: {reason}'
                  f'\nUnmuted by: {interaction.user.mention}', discord.Color.yellow())

    except discord.Forbidden:
        await interaction.edit_original_response(content="***I*** don't have permission to unmute this user. "
                                                         "\nPlease contact the server owner or administrator.",)

    except Exception as e:
        await interaction.edit_original_response(content=f"Error: {e}")


@bot.command()
async def echo(ctx, *args):
    await ctx.message.delete()
    await ctx.channel.send(*args)

# @bot.command()
# async def request(ctx, text):
#     response = requests.post("https://api.opencaptcha.io/captcha", json=
#   {
#    "text":str(text),
#   "difficulty": 0,
#   "width":800,
#   "height":200,},headers={"accept": "application/json"})
#     await ctx.message.reply(content=f"Status {response.status_code}", file=discord.File(io.BytesIO(response.content), f"captcha.png"))

@bot.command()
async def help(ctx, command=None):
    embed = None
    if command is None:
        embed = discord.Embed(title='Command Usage', description='Help Command Usage: '
                                                         '\n``.help [COMMAND]``'
                                                         '\nE.g: ``.help echo``'
                                                         '\n\nOther usages may include ``.help Difficulty``'
                                                            '\n\nHelp Command Description:'
                                                                 '\nShows the bot commands and command usages.', color=embed_blue)
    elif command and command.lower() == 'echo':
        embed = discord.Embed(title='Command Usage', description='Echo Command Usage:'
                                                                 '\n``.echo [Test]``'
                                                                 '\n E.g ``.echo Hello, World!``'
                                                                 '\n\nEcho Command Description:'
                                                                 '\nCopies the users text, sends it, and deletes the original message.',
                                                                 color=embed_blue)
    elif command and command.lower() == 'difficulty':
        embed = discord.Embed(title='Command Usage', description='Difficulty Information:'
                                                                 '\n\nDifficulty is a required argument when setting-up the bot.'
                                                                 '\nThere are 5 levels of difficultly, most are self-explanatory'
                                                                 '\n```Minimal: Minimal distortion'
                                                                 '\nBasic: Small amounts of distortion'
                                                                 '\nModerate: Normal amounts of distortion'
                                                                 '\nChallenging: Higher amounts of distortion.'
                                                                 '\nDynamic: Changes depending on user (READ BELOW)```'
                                                                 '\n\n Dynamic Difficulty'
                                                                 '\n Dynamic difficulty runs a check on each user when verifying,'
                                                                 'some checks include: no avatar/profile picture, young account (<60 days), and more.'
                                                                 'The amount of "flags" (failed checks) a user has, the harder the difficulty.',
                                                                 color=embed_blue)
    elif command and command.lower() in ['mute', 'unmute', 'timeout', 'untimeout']:
        embed = discord.Embed(title='Command Usage', description='Command Information:'
                                                                 '\n\nMuting forbids a member from sending messages, join voice channels,'
                                                                 ' reacting to messages, etc.'
                                                                 '\nYou can mute a member for a set amount of time (Min 1 minute).'
                                                                 '\n\nTo **mute** a member run ``/mute [MEMBER] [REASON] [LENGTH]``'
                                                                 '\nTo **un**mute a member run ``/unmute [MEMBER] [REASON]`` ',
                                                                 color=embed_blue)
    elif command:
        embed = discord.Embed(title='Message', description='Command not found:'
                                                           f'\n\n No command ``{command}`` was found, check for any typos.'
                                                           f'\n\n If the spelling is correct, ensure the command belongs to this bot (<@{bot.application_id}>)'
                                                           f'\n\n If the command does belong to this bot, consider contacting the bot owner.',color=embed_blue)

    await ctx.message.reply(embed=embed, delete_after=20)
    await asyncio.sleep(20)
    try:
        await ctx.message.delete()
    except:
        pass

@bot.event
async def on_message(message: discord.Message):
    print(f"my name is {message.author.name} yo")
    await bot.process_commands(message)

@bot.event
async def on_ready():
    await tree.sync()
    FormattedTime = f"{datetime.now().day}{['th', 'st', 'nd', 'rd', 'th', 'th', 'th', 'th', 'th', 'th'][datetime.now().day % 10]} {datetime.now().strftime('%b, %Y, %I:%M%p').lstrip('0')}"
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name=".help (Made by Pingu ❤️)", url='https://yt3.googleusercontent.com/8cgZMlfbExlkCdKjgJjxmHqa80xJ6WByNIbayrhS3AN3TbumcJO3TnujIq61nYh9vZWWMW7eUg=s160-c-k-c0x00ffffff-no-rj'))

    print(f'\n[{'-'*25}]'
          f'\n Shard ID: {bot.shard_id}'
          f'\n Shard Count: {bot.shard_count}'
          f'\n Latency: {round(bot.latency*1000)}ms'
          f'\n Commands: {len(bot.commands)}\n'
          f'[{'-'*25}]\n')
    print(f'Commands synced, {FormattedTime}.')

bot.run(TOKEN)
