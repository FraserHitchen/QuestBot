'''
Created on 7 Mar 2021

A quest utilities bot.

@author: Fraser
'''
from discord.ext import commands
import discord
import os
from dotenv import load_dotenv
from collections import Counter

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents(messages=True, guilds=True, members=True)
bot = commands.Bot(command_prefix='q!', intents=intents)
hunterRole = "Quest Hunter"
roleFormat = "lvl"

class questHelp(commands.MinimalHelpCommand):
    '''
    Changes help commands to use an embed.
    '''
    async def send_pages(self):
        destination = self.get_destination()
        for page in self.paginator.pages:
            emby = discord.Embed(description=page)
            await destination.send(embed=emby)
bot.help_command = questHelp()

@bot.event
async def on_ready():
    '''Code to run on bot startup'''
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the quest board"))
    
@bot.command(name='hunters')
async def hunters(ctx):
    '''
    Displays the current number of hunters, broken down by level.
    '''
    questHunters = []
    guild = ctx.channel.guild
    for member in guild.members:
        for role in member.roles:
            if role.name == hunterRole:
                questHunters.append(member)
    
    totalHunters = len(questHunters)
    hunterRoles = []
    for hunter in questHunters:
        for role in hunter.roles:
            hunterRoles.append(role.name)
    
    hunterRoles = dict(Counter(hunterRoles))
    hunterRoles = [(role, count) for role, count in hunterRoles.items() if roleFormat in role.lower()]
    hunterRoles = [(int(role[0].strip(f"{roleFormat} ")), role[1]) for role in hunterRoles]
    hunterRoles = sorted(hunterRoles)
    result = ""
    for role in hunterRoles:
        result += f"\n**Level {role[0]} Hunters:** {role[1]}"
        
    embed = discord.Embed(title="Quest Hunter Breakdown", description=f"Total Quest Hunters: {totalHunters}\n━━━━━━━━━━ {result}")
    embed.set_footer(text="q!hunters | Fraser") 
    await ctx.send(embed=embed)    
    
bot.run(TOKEN)