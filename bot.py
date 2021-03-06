'''
Created on 7 Mar 2021

A quest utilities bot.

@author: Fraser
'''
from discord.ext import commands
import discord
import os
import asyncio
import json
from dotenv import load_dotenv
from collections import Counter
import redis
import bot_utils as bu
import re
import requests
from discord.ext.commands.errors import CommandInvokeError

redis_server = redis.Redis()
load_dotenv()

try:
    TOKEN = str(redis_server.get('DISCORD_TOKEN').decode('utf-8'))
except:
    TOKEN = os.getenv('DISCORD_TOKEN')
    print('Token accepted from env.')
else:
    print('Token accepted from redis.')
intents = discord.Intents(messages=True, guilds=True, members=True, reactions=True, emojis=True)
bot = commands.Bot(command_prefix='q!', intents=intents)
quest_hunter_roles = {}
role_format = 'lvl'

quest_hunters = []
hunter_roles = []
total_hunters = 0

react_messages = {}
react_emojis = {}
hunter_reactions = {}
react_channels = {}

class quest_help(commands.MinimalHelpCommand):
    '''Changes help commands to use an embed.'''
    async def send_pages(self):
        destination = self.get_destination()
        emby = discord.Embed(description='')
        for page in self.paginator.pages:
            emby.description += page
        await destination.send(embed=emby)
            
bot.help_command = quest_help(no_category = 'Commands')
        
@bot.event
async def on_ready():
    '''Code to run on bot startup. 
    
    Takes reaction role input from a JSON file generated by the setup function.
    '''
    global react_messages
    global react_emojis
    global hunter_roles
    global hunter_reactions
    
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name='for quests | q!help'))

    react_input = {}
    for guild in bot.guilds:
        quest_hunter_roles[guild.id] = discord.utils.get(guild.roles,name='Quest Hunter')
        react_input[guild.id] = {}
        if os.path.exists(f'{guild.id}.txt') and os.path.getsize(f'{guild.id}.txt') != 0:
            with open(f'{guild.id}.txt') as json_file:
                react_input[guild.id] = json.load(json_file)
                print(f'Successful input from {guild.name}: {react_input[guild.id]}')
                
                react_emojis[guild.id] = react_input[guild.id]['react_emoji'] 
                react_channels[guild.id] = discord.utils.get(guild.text_channels, id=react_input[guild.id]['channel_id'])
                react_messages[guild.id] = await react_channels[guild.id].fetch_message(react_input[guild.id]['message_id'])
                hunter_reactions[guild.id] = discord.utils.get(react_messages[guild.id].reactions, emoji=react_emojis[guild.id])
        else:
            print(f'Invalid or empty json for {guild.name}')
        
def approved_only():
    async def predicate(ctx):
        approved_roles = ['The Power Rangers', 'Moderator', 'Bot Team']
        for role in ctx.author.roles:
            if role.name in approved_roles:
                return True
        raise commands.MissingPermissions('')
    return commands.check(predicate)

commands.has_permissions(administrator=True), commands.is_owner(), commands.has_role('Bot Team')

def dm_only():
    async def predicate(ctx):
        approved_roles = ['The Power Rangers', 'Moderator', 'Bot Team', 'Dungeon Master', 'Trainee DM']
        for role in ctx.author.roles:
            if role.name in approved_roles:
                return True
        raise commands.MissingPermissions('')
    return commands.check(predicate)

def cat_and_approved():
    async def predicate(ctx):
        approved_roles = ['The Power Rangers', 'Moderator', 'Bot Team', 'Character Approval Team']
        for role in ctx.author.roles:
            if role.name in approved_roles:
                return True
        raise commands.MissingPermissions('')
    return commands.check(predicate)
        
    
def get_hunters(ctx):
    '''Get a list of all members with the quest hunter role.'''  
    guild = ctx.channel.guild
    global quest_hunters
    for member in guild.members:
        for role in member.roles:
            if role == quest_hunter_roles[guild.id]:
                quest_hunters.append(member)

                
    
def format_roles(hunters):
    ''' Get a list of tuples with the number of occurrences of each level.
    
    Takes a list of members, counts the number of times each level role comes up and outputs that in a tuple where the first element is the level and the second value is the number of occurrences.
    '''
    global hunter_roles
    global total_hunters
    total_hunters = len(hunters)
    for hunter in hunters:
        for role in hunter.roles:
            hunter_roles.append(role.name)
           
    hunter_roles = dict(Counter(hunter_roles))
    hunter_roles = [(role, count) for role, count in hunter_roles.items() if role_format in role.lower()]
    hunter_roles = [(int(role[0].strip(f'{role_format} ')), role[1]) for role in hunter_roles]
    hunter_roles = sorted(hunter_roles)  

    
@bot.command(name='hunters')
@dm_only()
async def hunters(ctx):
    '''Display the current number of hunters, broken down by level.'''
    global quest_hunters
    global hunter_roles
    global total_hunters
    
    quest_hunters = []
    hunter_roles = []
    
    await bu.safe_message_delete(ctx)
    
    get_hunters(ctx)
    format_roles(quest_hunters)
    
    result = ''
    for role in hunter_roles:
        result += f'\n**Level {role[0]} Hunters:** {role[1]}'
        
    embed = discord.Embed(title='Quest Hunter Breakdown', description=f'Total Quest Hunters: {total_hunters}\n?????????????????????????????? {result}')
    embed.set_footer(text='q!hunters | Fraser') 
    await ctx.send(embed=embed)
    

async def update_react(ctx):
    '''Update the react variables with any new reactions.'''
    
    guild = ctx.guild
    global react_messages
    global hunter_reactions
    
    react_messages[guild.id], hunter_reactions[guild.id] = await bu.update_reaction(react_messages[guild.id], react_emojis[guild.id])
    
    
@bot.command(name='setup')
@approved_only()
async def setup(ctx, message_link):
    '''Set up a new quest hunter reaction role. Info is stored as a JSON file.
    
    This command requires 1 argument which is a link to the message you want users to react to.
    
    After sending the command you react to the bot's post to set the emoji you want.
    '''
    global react_messages
    global react_emojis
    global hunter_reactions
    
    guild_id, channel_id, message_id = await bu.convert_link(ctx, message_link)
    guild = bot.get_guild(guild_id)
    if guild != ctx.guild:
        raise commands.CommandInvokeError('Attempted prune for message in different guild')
    channel = bot.get_channel(channel_id)
    react_messages[guild.id] = await channel.fetch_message(message_id)
    
    await bu.safe_message_delete(ctx)
    
    react_embed = discord.Embed(title='React here!', description=f'Message link accepted! Now react to this post with the emoji you wish to use.')
    react_embed.set_footer(text='q!setup | Fraser')
    react_embed = await ctx.send(embed=react_embed)
    
    def check(reaction, user):
        print(reaction.message)
        return (user == ctx.message.author and reaction.message == react_embed)
    
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        print('Unsuccessful setup: Timeout')
        timeout_embed = discord.Embed(title='Timeout', description=f'Setup timed out. Please try again.')
        timeout_embed = await ctx.send(embed=timeout_embed)
        await asyncio.sleep(5) 
        await timeout_embed.delete()
    else:
        await react_embed.delete()
        react_emojis[guild.id] = reaction.emoji
        await react_messages[guild.id].add_reaction(react_emojis[guild.id])
           
    await update_react(ctx)
        
    react_output = {'message_id':react_messages[guild.id].id,'channel_id':react_messages[guild.id].channel.id, 'react_emoji':str(react_emojis[guild.id])}
    print(f'Successful setup, output: {react_output}')
    
    setup_embed=discord.Embed(title='Successful Setup', description=f'Quest hunter role reaction successfully set up.\n??????????????????????????????\nMessage: {react_messages[guild.id].content}\nChannel: {react_messages[guild.id].channel.name}\nEmoji: {react_emojis[guild.id]}')
    setup_embed.set_footer(text='q!setup | Fraser')
    setup_embed = await ctx.send(embed = setup_embed)
        
    with open(f'{guild.id}.txt', 'w') as outfile:
        json.dump(react_output, outfile)
        
        
@bot.command(name='reset')
@approved_only()
async def reset(ctx):
    '''Reset the react variables and empty the text file.'''
    global react_messages
    global react_emojis
    global hunter_reactions
    
    await bu.safe_message_delete(ctx)
    
    guild = ctx.guild

    bot_message = await ctx.send(embed=discord.Embed(title='Reaction Role Reset', description=f'Are you sure you want to reset the reaction role?'))
    await bot_message.add_reaction('????')
    await bot_message.add_reaction('????')
    
    def check(reaction, user):
        return user == ctx.message.author and (str(reaction.emoji) == '????' or str(reaction.emoji) == '????')
    # Checks for user confirming or denying the rest
    try:
        reaction, user = await bot.wait_for('reaction_add', timeout=60.0, check=check)
    except asyncio.TimeoutError:
        print('timeout')
    else:
        if reaction.emoji == '????':
            await bot_message.delete()
            # Removes bot reaction, sets all reaction variables to None and clears the text file
            await react_messages[guild.id].remove_reaction(react_emojis[guild.id], bot.user)
            react_messages[guild.id] = react_emojis[guild.id] = hunter_reactions[guild.id] = None
            open(f'{guild.id}.txt', 'w').close()
            print(f'Successful reset on {guild.name}')
            
            reset_embed = discord.Embed(title='Successful Reset', description=f'The quest hunter reaction has successfully been reset.')
            reset_embed.set_footer(text='q!reset | Fraser') 
            await ctx.send(embed=reset_embed)
            
            
        elif reaction.emoji == '????':
            await bot_message.delete()
    
@bot.command(name='prune')
@approved_only()
async def prune(ctx, message_link : str):
    '''Prune reactions on a message from users which are no longer on the server.'''
    await bu.safe_message_delete(ctx)

    guild_id, channel_id, message_id = await bu.convert_link(ctx, message_link)
    guild = bot.get_guild(guild_id)
    if guild != ctx.guild:
        raise commands.CommandInvokeError('Attempted prune for message in different guild')
    channel = bot.get_channel(channel_id)
    message = await channel.fetch_message(message_id)

    removed_users = {}
    
    # Interates through all reactions
    for reaction in message.reactions:
        
        removed_users[reaction.emoji]=[]
        # Gets all the members that have reacted to the message and flattens into a list
        reactors = await reaction.users().flatten()
        for user in reactors:
            # Checks if members in the list have left the server, and removes their reaction if so
            if guild.get_member(user.id) is None and user != bot.user:
                await reaction.remove(user)
                removed_users[reaction.emoji].append(f'{user.name}#{user.discriminator}')   
                     
    # Get total number of leavers by removing duplicates
    leavers = []        
    for key in removed_users:
        for value in removed_users[key]:
            if value not in leavers:
                leavers.append(value)
    print(f'Users no longer in server: {leavers}')
    total_removed = len(leavers)
    
    # Create embed with a field for each reaction               
    result = f'A total of {total_removed} users were detected as no longer being on the server, and their reactions were removed.\n\n**Removals:**\n??????????????????????????????'
    prune_embed=discord.Embed(title='Prune Complete', description=f'{result}')
    for key in removed_users:
        field_name = key
        field_value = ''
        for value in removed_users[key]:
            field_value += f'{value}\n'
        if field_value == '': field_value = 'None'
        prune_embed.add_field(name=field_name, value=field_value, inline='False')
    prune_embed.set_footer(text='q!prune | Fraser') 
    await ctx.send(embed=prune_embed)

@bot.command(name='kill')
@approved_only()
async def kill(ctx):
    '''Kills the bot.'''
    await bot.close()
    
@bot.command(name='stats')
@cat_and_approved()
async def stats(ctx, channel_id = int('777981024860241920')):
    '''Print server stats.'''
    guild = ctx.guild
    channel = guild.get_channel(channel_id)
    messages = await channel.history(limit=20, oldest_first=True).flatten()
    
    # Remove extra text
    messages[0].content = re.split(r'(Aarakocra)', messages[0].content)
    messages[0].content = messages[0].content[1] + messages[0].content[2]
    
    
    messages[2].content = messages[2].content.replace('|B', '| B')
    messages[2].content = re.split(r'(Barbarian)', messages[2].content)
    messages[2].content = messages[2].content[1] + messages[2].content[2]
    print(messages[2].content)
    
    # Races and Classes
    reactions = []
    message_text = []
    for message in messages[0:3]:
        reactions.append(message.reactions)
        message_text.append(message.content)
        
    split_text = []    
    for message in message_text:
        split_text.append(message.split(' | '))   
    
    react_counts = []
    for text_list, reaction_list in zip(split_text, reactions):
        react_list = []
        for text, reaction in zip(text_list, reaction_list):
            react_list.append((text, reaction.count))
        react_counts.append(react_list)
        
    categories = ['Races', 'Races', 'Classes']
    
    result_dict = {}
    for category, count in zip(categories, react_counts):
        if category not in result_dict:
            result_dict[category] = []
        result_dict[category].append(count)
        
    for key in result_dict:
        flat_list = [item for sublist in result_dict[key] for item in sublist]
        result_dict[key] = flat_list
    
    # Add artificer to classes
    result_dict['Classes'].append(('Artificer :gear:', messages[5].reactions[0].count))
    
    # Level stuff
    level_reactions = messages[3].reactions
    result_dict['Levels']=[]
    for reaction in level_reactions:
        result_dict['Levels'].append((reaction.emoji,reaction.count))
    
    categories = ['Races', 'Classes', 'Levels']
    
    # Output embed
    output_str = f''
    stat_embed=discord.Embed(title='Server Stats', description=f'{output_str}')
    for category in categories:
        field_name = category
        field_value = ''
        for value in result_dict[category]:
            field_value += f'{value[0]}: {value[1]}\n'
        if field_value == '': field_value = 'None'
        stat_embed.add_field(name=field_name, value=field_value, inline='True')
    stat_embed.set_footer(text='q!stats | Fraser') 
    await ctx.send(embed=stat_embed)

@bot.command(name='release')
@approved_only()
async def release(ctx):  
    '''Print the latest release information.'''
    await bu.safe_message_delete(ctx)
    response = requests.get('https://api.github.com/repos/FraserHitchen/QuestBot/releases/latest')
    release_embed = discord.Embed(title=f'{response.json()["name"]}', description=f'{response.json()["body"]}')
    release_embed.set_footer(text=f'{response.json()["html_url"]}') 
    await ctx.send(embed=release_embed)
    
@bot.command(name='add_questers')
@approved_only()
async def add_questers(ctx, message_link, role):
    role = int(role.strip('<@&>')) 
    await bu.safe_message_delete(ctx)

    guild_id, channel_id, message_id = await bu.convert_link(ctx, message_link)
    guild = bot.get_guild(guild_id)
    channel = bot.get_channel(channel_id)
    message = await channel.fetch_message(message_id)
    role = guild.get_role(role)
    if role >= discord.utils.get(guild.roles,name="Bots"):
        raise CommandInvokeError
    
    reaction_users = await message.reactions[0].users().flatten()
    
    users = ''
    count = 0
    for user in reaction_users:
        if user != message.author and role not in user.roles:
            await user.add_roles(role)
            count += 1
            users += f'{user.name}#{user.discriminator}\n'
    print(f'q!add_quests called by {ctx.author}. {role} added to:\n {users}')
    
    quest_embed=discord.Embed(title='Quest Role Added', description=f'The role {role} has successfully been added to {count} users.\n{message_link}\n??????????????????????????????\n{users}')
    quest_embed.set_footer(text='q!add_questers | Fraser')
    quest_embed = await ctx.send(embed = quest_embed)

@bot.event
async def on_raw_reaction_add(payload):
    '''Give user quest hunter role if they react to a reaction role.'''
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    
    check_emoji = None
    check_id = None
    try:
        check_emoji = react_emojis[guild.id]
        check_id = react_messages[guild.id].id
    except:
        pass
        

    if user != bot.user:
        if str(payload.emoji) == str(check_emoji) and payload.message_id == check_id:  
            await user.add_roles(quest_hunter_roles[guild.id])
            print(f'{quest_hunter_roles[guild.id].name} role added to {user} on {guild.name}')
                 
@bot.event
async def on_raw_reaction_remove(payload):
    '''Remove user quest hunter role if they remove reaction to a reaction role.'''
    guild = bot.get_guild(payload.guild_id)
    user = guild.get_member(payload.user_id)
    
    check_emoji = None
    check_id = None
    try:
        check_emoji = react_emojis[guild.id]
        check_id = react_messages[guild.id].id
    except:
        pass
        
    if user != bot.user and user is not None:
        if str(payload.emoji) == str(check_emoji) and payload.message_id == check_id: 
            await user.remove_roles(quest_hunter_roles[guild.id])
            print(f'{quest_hunter_roles[guild.id].name} role removed from {user} on {guild.name}')
            



            
@bot.event
async def on_command_error(ctx, error):
    '''Handle command errors.'''
    print(f'Command q!{ctx.command} called by {ctx.author} raised error: {error}')
       
    # Prevents commands with local handlers being handled here
    if hasattr(ctx.command, 'on_error'):
            return
           
           
    if isinstance(error, commands.CommandNotFound):
        error_embed = discord.Embed(title='Command Not Found', description=f'No such command exists. Use `q!help` for a list of commands.') 
           
    elif isinstance(error, commands.MissingRequiredArgument):
        error_embed = discord.Embed(title='Missing Argument', description=f'You are missing a required argument for this command. Use `q!help {ctx.command}` for help.')      
           
    elif isinstance(error, commands.MissingPermissions):
        error_embed = discord.Embed(title='Missing Permissions', description=f'You do not have the required permissions to run that command.')
            
    else:
        error_embed = discord.Embed(title='Error', description=f'An error occurred when running this command. Use `q!help` for help.')
         
    error_embed.set_footer(text='q!help | Fraser') 
    error_embed = await ctx.send(embed=error_embed)
    await asyncio.sleep(5) 
    await error_embed.delete()

bot.run(TOKEN)