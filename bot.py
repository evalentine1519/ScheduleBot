import os
import random
from dotenv import load_dotenv
import time
from datetime import datetime
import discord
import json
import logging

# 1
from discord.ext import commands, tasks

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
intents = discord.Intents.default()
intents.members = True

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

@bot.command(name='hello', help="Pings a given user, if they exist on the server")
async def hello(ctx, username=None):
    command_guild = str(ctx.guild.id)
    command_channel = str(ctx.channel.id)

    logger.info(command_guild)
    logger.info("Command sent from channel with ID: " + command_channel)

    if username is None:
        response = f'User {username} does not exist!'
        await ctx.send(response)

    #id = ctx.message.guild.id
    #guild = bot.get_guild(id)
    guild = bot.get_guild(int(command_guild))
    user = discord.utils.get(guild.members, name=username)
    print(username)
    print('user id is: ' + str(user.id))

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
    print(eventlist)
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
        #for item in content:
            #contentstr = contentstr + item + ' '
        #timeentry = {'time': contentstr}
        print(type(content))
        print(content)
        contentstr = ' '.join(content)
        #timeobj = datetime.strptime(contentstr.strip(), "%m/%d/%Y %I:%M %p")
        #timestmp = int(timeobj.timestamp())
        #timeentry = {'time': timestmp}

        timestmp = int((datetime.strptime(contentstr.strip(), "%m/%d/%Y %I:%M %p")).timestamp())
        timeentry = {'time': timestmp}
        eventlist[command_guild][eventname].update(timeentry)
        save(eventlist)

        #eventlist[event].update(timeentry)
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
        logger.info('content[0] is ' + content[0])
        logger.info('content[1] is ' + str(type(content[1])))

        if len(content)>2:
            response = "Error: 'auto' only takes two arguments: 'yes or no' and an optional argument for the reminder hour (24-hour format)"
            await ctx.send(response)
        else:
            logger.info(content)
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
    logger.info('Running loop')
    now = datetime.now()
    now_timestamp = datetime.timestamp(now)

    for guild_id in eventlist:
        logger.info(f'Eventlist is {eventlist}')
        guild = bot.get_guild(int(guild_id))
        #channelname = eventlist[guild_id][]
        #channel = discord.utils.get(guild.text_channels, name='general')
        logger.info(f'Guild ID of {guild} is {guild.id}')

        for eventname in eventlist[guild_id]:
            channelname = eventlist[guild_id][eventname]['reminderchannel']
            channel = discord.utils.get(guild.text_channels, name=f'{channelname}')
            logger.info(f'Channel ID is {channel.id}')

            logger.info(eventlist[guild_id][eventname]['auto'][0])
            logger.info('type is ' + str(type(eventlist[guild_id][eventname]['auto'][0])))
            if eventlist[guild_id][eventname]['auto'][0] == True:
                stored_timestamp = int(eventlist[guild_id][eventname]['time'])
                logger.info('Hour to check against is ' + str(eventlist[guild_id][eventname]['auto'][1]))
                logger.info('Type is ' + str(type(eventlist[guild_id][eventname]['auto'][1])))
                if (stored_timestamp - now_timestamp < 86400) and (now.hour == eventlist[guild_id][eventname]['auto'][1]):
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
                    await channel.send(response)




bot.run(TOKEN)
