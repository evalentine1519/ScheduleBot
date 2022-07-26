import os
import random
from dotenv import load_dotenv
import time
from datetime import datetime
import discord
import json
import logging
from random import randint
from requests import get

# 1
from discord.ext import commands, tasks

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
TENOR_API = os.getenv('TENOR_API')
intents = discord.Intents.default()
intents.members = True

giflist = ['https://c.tenor.com/viw-vfM60tUAAAAC/spongebob-art-thou-feeling.gif',
            'https://c.tenor.com/COIkgK11ZcwAAAAC/dungeons-and-dragons-tbbt.gif',
            'https://c.tenor.com/VBmD41K54dEAAAAd/can-we-play-stranger-things.gif',
            'https://c.tenor.com/5beO3hQkNqMAAAAd/criticalrole-critrole.gif',
            'https://c.tenor.com/ijrIbEWVPDIAAAAC/i-want-you-gandalf.gif',
            'https://c.tenor.com/tmaf0isifhwAAAAC/beholder-monster.gif',
            'https://c.tenor.com/Aa4rQBXubYcAAAAd/dn-d.gif',
            'https://c.tenor.com/E3AinNipE1IAAAAC/batman-mr-freeze.gif'
            ]

# 2
logging.basicConfig(level=logging.INFO, filename='bot.log', format='%(asctime)s :: %(levelname)s :: %(message)s')
logger = logging.getLogger('ScheduleBot')
client = discord.Client()
bot = commands.Bot(command_prefix='!', intents=intents)
try:
    with open("dictionary.txt") as json_dict:
        eventlist = json.load(json_dict)
        json_dict.close()
    logger.info("Loading dictionary from file successful!")
except:
    eventlist = {}
    logger.info("Loading dictionary from file failed!")

#3 - Helper functions
def save(dict_file):
    with open('dictionary.txt', 'w') as json_dict:
        json_dict.write(json.dumps(dict_file))
        json_dict.close()

def get_gif(search_term, limit):
    #searches tenor for a given search term for a given number of results, returns a random gif url from those results
    r = get(f'https://tenor.googleapis.com/v2/search?q={search_term}&key={TENOR_API}&media_filter=gif&limit={limit}')
    r_dict = json.loads(r.content)
    index = randint(0, (len(r_dict['results'])-1))
    result = r_dict['results'][index]['media_formats']['gif']['url']
    return result

def get_spell(name):
    if len(name) > 1:
        name = '-'.join(name)
    else:
        name = str(name[0])

    logger.info(type(name))
    logger.info(name)
    spell = get(f'https://www.dnd5eapi.co/api/spells/{name}')
    logger.info(spell)

    if spell.status_code == 404:
        return "That spell does not exist"

    spell = json.loads(spell.content)
    is_ritual = spell['ritual']
    if spell['level'] == 1:
        level = f"{spell['level']}st-level"
    elif spell['level'] == 2:
        level = f"{spell['level']}nd-level"
    elif spell['level'] == 3:
        level = f"{spell['level']}rd-level"
    else:
        level = f"{spell['level']}th-level"
    level_info = f"{level} {spell['school']['name']}"

    if is_ritual == True:
        level_info = level_info + " (ritual)"

    component_info = ', '.join(spell['components'])

    try:
        spell['material']
    except:
        pass
    else:
        component_info = component_info + f" ({spell['material']})"

    spell_text = f"***{spell['name']}***\n*{level_info}*\n\n**Casting Time:** {spell['casting_time']}\n**Range:** {spell['range']}\n**Components:** {component_info}\n**Duration:** {spell['duration']}\n\n{' '.join(spell['desc'])}"
    logger.info(spell_text)

    return spell_text

@bot.event
async def on_ready():
    logger.info(f'{bot.user.name} has connected to Discord!')
    reminder_check.start()

@bot.event
async def on_guild_join(guild):
    logger.info("Joined guild: " + str(guild))
    command_guild = str(guild.id)
    eventlist.update({f'{command_guild}': {}})
    save(eventlist)

@bot.command(name='shitpost')
async def shitpost(ctx, term='dnd', limit='20'):
    logger.info('trying to shitpost')
    response = get_gif(term, limit)
    await ctx.send(response)

@bot.command(name='5e')
async def get_rules(ctx, resource, *spellname):
    logger.info(resource)
    if resource == 'spell':
        logger.info('getting spell')
        response = get_spell(spellname)
        logger.info('spell gotten')
    await ctx.send(response)

@bot.command(name='hello', help="Pings a given user, if they exist on the server")
async def hello(ctx, username=None):
    command_guild = str(ctx.guild.id)
    command_channel = str(ctx.channel.id)

    if username is None:
        response = f'User {username} does not exist!'
        await ctx.send(response)

    guild = bot.get_guild(int(command_guild))
    user = discord.utils.get(guild.members, name=username)

    response = f'<@{user.id}>'
    await ctx.send(response)

@bot.command(name='addevent', help='Adds an event to the schedule. Usage: !addevent <event>')
async def addevent(ctx, eventname):
    command_guild = str(ctx.guild.id)

    if eventname in eventlist[command_guild].keys():
        response = f'Event {eventname} already exists!'
        await ctx.send(response)
    else:
        eventlist[command_guild].update({f'{eventname}': {}})
        save(eventlist)
        response = f'Event {eventname} added!'
        await ctx.send(response)

@bot.command(name='eventlist', help="Lists the names of all current events")
async def listevents(ctx, *args):
    command_guild = str(ctx.guild.id)

    try:
        logger.info(eventlist[command_guild])
    except:
        eventlist.update({f'{command_guild}': {}})
        logger.info(eventlist[command_guild])

    if len(args) == 0:
        if len(eventlist[command_guild]) == 0:
            await ctx.send('There are no scheduled events in the list!')
        else:
            events = '\n - '.join(key for key, value in eventlist[command_guild].items())
            await ctx.send(f'Events:\n - {events}')
    else:
        await ctx.send('nope')

@bot.command(name='when', help='Displays when the asked-for event is scheduled to occur. Usage: !when <event>')
async def when(ctx, eventname):
    command_guild = str(ctx.guild.id)

    if eventname in eventlist[command_guild].keys():
        timestmp = eventlist[command_guild][eventname]['time']
        response = f'{eventname} will happen on <t:{timestmp}:F>'
        await ctx.send(response)
    else:
        response = f'Event {eventname} does not exist!'
        await ctx.send(response)

@bot.command(name='time', help='Displays the current local time')
async def timeGetter(ctx):
    timestamp = int(time.time())
    response = f'current time is <t:{timestamp}:F>'
    await ctx.send(response)

@bot.command(name='set', help="Sets various parameters for a given event. Usage: !set <command> <event> <parameters>\n Time parameter must be set as: mm/dd/yyyy hh:mm AM/PM")
async def set(ctx, command, eventname, *content):
    id = ctx.message.guild.id
    guild = bot.get_guild(id)
    contentstr = ''
    contentlist = []
    command_guild = str(ctx.guild.id)

    logger.info("Guild ID for the guild !set was sent from is: " + command_guild)

    if command == 'time':
        contentstr = ' '.join(content)

        timestmp = int((datetime.strptime(contentstr.strip(), "%m/%d/%Y %I:%M %p")).timestamp())
        timeentry = {'time': timestmp}
        eventlist[command_guild][eventname].update(timeentry)
        save(eventlist)

    elif command == 'who':
        eventlist[command_guild][eventname]['who'] = []
        wholist = eventlist[command_guild][eventname]['who']
        if content[0] == 'everyone':
            wholist.append('@everyone')
        else:
            for index, item in enumerate(content):
                user = str(discord.utils.get(guild.members, name=item))
                userTuple = (item, user)
                wholist.append(userTuple)
        save(eventlist)

    elif command == "auto":

        if len(content)>2:
            response = "Error: 'auto' only takes two arguments: 'yes or no' and an optional argument for the reminder hour (24-hour format)"
            await ctx.send(response)
        else:
            if content[0].lower() == 'yes':
                if len(content) == 2:
                    eventlist[command_guild][eventname]['auto'] = [True, int(f'{content[1]}')]
                else:
                    eventlist[command_guild][eventname]['auto'] = [True, 12]
                eventlist[command_guild][eventname]['reminderchannel'] = 'general'
            elif content[0].lower() == 'no':
                eventlist[command_guild][eventname]['auto'] = False
            else:
                response = "Error: argument for 'auto' must be either 'yes' or 'no'"
                await ctx.send(response)
            save(eventlist)

    elif command == 'reminderchannel':
        if len(content) > 1:
            response = "Error: Channel name must be one word"
            await ctx.send(response)
        else:
            guild = bot.get_guild(int(command_guild))
            channel = discord.utils.get(guild.text_channels, name=f'{content[0]}')
            if channel == None:
                response = "Error: Channel does not exist in this server."
                await ctx.send(response)
            else:
                eventlist[command_guild][eventname]['reminderchannel'] = content[0]
                response = f"Automatic reminder will be sent to {content[0]}"
                await ctx.send(response)
        save(eventlist)
        return


    response = f'{command} for {eventname} set!'
    await ctx.send(response)

@bot.command(name='who', help="Enter an event's name to see who's attending Usage: !who <event>")
async def getWho(ctx, eventname=None):
    command_guild = str(ctx.guild.id)

    who = eventlist[command_guild][eventname]['who']
    content = []

    if eventname is None:
        response = f"Event {eventname} doesn't exist!"
        await ctx.send(response)

    if who[0] == '@everyone':
        response = f'{eventname} is scheduled for everyone'
    else:
        for people in who:
            content.append(people[0])
        wholist = ', '.join(content)
        response = f'{eventname} is scheduled for the following people: {wholist}'

    await ctx.send(response)

@bot.command(name='remind', help='Ping the users attending a given event. Usage: !remind <event>')
async def reminder(ctx, eventname=None):
    command_guild = str(ctx.guild.id)

    if eventname is None:
        response = "You must supply an event to remind people of!"
        await ctx.send(response)
    else:
        who = eventlist[command_guild][eventname]['who']
        timestamp = eventlist[command_guild][eventname]['time']
        id = ctx.message.guild.id
        guild = bot.get_guild(id)

        if who[0] == '@everyone':
            response = f"@everyone Reminder, {eventname} is scheduled for <t:{timestamp}:F>"
            await ctx.send(response)
        else:
            wholist = []
            for people in who:
                user = discord.utils.get(guild.members, name=people[0])
                wholist.append(f'<@{user.id}>')
            whostr = ' '.join(wholist)
            response = f"{whostr} Reminder, {eventname} is scheduled for <t:{timestamp}:F>"
            await ctx.send(response)

@tasks.loop(hours=1)
async def reminder_check():
    #Reconfigure so that loop calls a reminder helper function instead of sending reminder from the loop-
    #sending a message from the loop makes it exit after it reminds about the first event it encounters
    logger.info('Running reminder loop')
    now = datetime.now()
    now_timestamp = datetime.timestamp(now)

    for guild_id in eventlist:
        guild = bot.get_guild(int(guild_id))

        for eventname in eventlist[guild_id]:
            channelname = eventlist[guild_id][eventname]['reminderchannel']
            channel = discord.utils.get(guild.text_channels, name=f'{channelname}')

            if eventlist[guild_id][eventname]['auto'][0] == True:
                stored_timestamp = int(eventlist[guild_id][eventname]['time'])
                if (stored_timestamp - now_timestamp < 86400 and stored_timestamp - now_timestamp > 0) and (now.hour == eventlist[guild_id][eventname]['auto'][1]):
                    who = eventlist[guild_id][eventname]['who']

                    if who[0] == '@everyone':
                        whostr = '@everyone'
                    else:
                        wholist = []
                        for people in who:
                            user = discord.utils.get(guild.members, name=people[0])
                            wholist.append(f'<@{user.id}>')
                        whostr = ' '.join(wholist)

                    response = f'{whostr} Reminder, {eventname} is scheduled for <t:{stored_timestamp}:F>'
                    logger.info(eventname)
                    if eventname == 'dnd':
                        index = randint(0, (len(giflist)-1))
                        response = response + '\n' + giflist[index]
                    await channel.send(response)

@reminder_check.before_loop
async def before_reminder_check():
    await bot.wait_until_ready()




bot.run(TOKEN)
