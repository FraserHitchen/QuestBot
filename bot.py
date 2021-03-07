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
'''bot.remove_command('help')'''""
roleFormat = "lvl"

@bot.event
async def on_ready():
    '''Code to run on bot startup'''
    print(f'{bot.user} has connected to Discord!')
    await bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="the quest board"))
    
@bot.command(name='hunters')
async def hunters(ctx):
    questHunters = []
    guild = ctx.channel.guild
    for member in guild.members:
        for role in member.roles:
            if role.name == "Quest Hunter":
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
    await ctx.send(embed=discord.Embed(title="Quest Hunter Breakdown", description=f"Total Quest Hunters: {totalHunters} {result}"))    
    
bot.run(TOKEN)