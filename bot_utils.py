'''
Created on 24 May 2021

@author: Fraser
'''

import discord
import asyncio

async def fetch_message_util(ctx, bot, message_id, channel_id=None):
    '''Fetch a message from the context channel or another channel.'''
    if channel_id:
        channel_id = int(channel_id[0])
        channel = bot.get_channel(channel_id)
        message = await channel.fetch_message(message_id)
    else:
        message = await ctx.fetch_message(message_id)

    return message

async def update_reaction(message, emoji):
    '''Update a reaction so it has all currents reactions.'''
    channel = message.channel
    message_id = message.id
    
    message = await channel.fetch_message(message_id)
    reaction = discord.utils.get(message.reactions, emoji=emoji)
    
    return message, reaction

async def input_to_id(ctx, inp):
    if isinstance(inp, int):
        return inp
    elif isinstance(inp, str):
        if inp[0:2] == '<#' or inp[0:2] == '<@&':
            inp = inp.strip('<#@&>')
            return int(inp)
        else:
            try:
                inp = int(inp)
            except:
                pass
            else:
                return inp
    embed = discord.Embed(title='Invalid Argument', description=f'The argument you entered was invalid. Make sure the argument you provide is in the correct format and try again.')
    input_embed = await ctx.send(embed=embed)
    await asyncio.sleep(5) 
    await input_embed.delete()
    
async def convert_link(ctx, inp):
    '''Get guild id, channel id and message id from a message link'''
    if inp[0:29] == 'https://discord.com/channels/':
        inp = inp[29:]
        result = inp.split('/')
        return int(result[0]), int(result[1]), int(result[2])
    else:
        raise ValueError('Input not a message link.')

async def safe_message_delete(ctx):
    if not isinstance(ctx.channel, discord.channel.DMChannel):
        await ctx.message.delete()
    
    