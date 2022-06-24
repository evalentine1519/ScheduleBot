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
    print("Loading dictionary from file successful!")
except:
    eventlist = {}
    print("Loading dictionary from file failed!")

#3 - Helper functions
def save(dict_file):
    with open('dictionary.txt', 'w') as json_dict:
        json_dict.write(json.dumps(dict_file))
        json_dict.close()



@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord!')
    reminder_check.start()

@bot.command(name='hello', help="Pings a given user, if they exist on the server")
async def hello(ctx, username=None):
    command_guild = ctx.guild.id

    logger.info(command_guild)

    if username is None:
        response = f'User {username} does not exist!'
        await ctx.send(response)

    id = ctx.message.guild.id
    guild = bot.get_guild(id)
    user = discord.utils.get(guild.members, name=username)
    print(username)
    print('user id is: ' + str(user.id))

    response = f'<@{user.id}>'
    await ctx.send(response)

@bot.command(name='addevent', help='Adds an event to the schedule. Usage: !addevent <event>')
async def addevent(ctx, eventname):
    if eventname in eventlist.keys():
        response = f'Event {eventname} already exists!'
        await ctx.send(response)
    else:
        eventlist.update({f'{eventname}': {}})
        save(eventlist)
        response = f'Event {eventname} added!'
        await ctx.send(response)

@bot.command(name='eventlist', help="Lists the names of all current events")
async def listevents(ctx, *args):
    print(eventlist)
    if len(args) == 0:
        if len(eventlist) == 0:
            await ctx.send('There are no scheduled events in the list!')
        else:
            events = '\n - '.join(key for key, value in eventlist.items())
            await ctx.send(f'Events:\n - {events}')
    else:
        await ctx.send('nope')

@bot.command(name='when', help='Displays when the asked-for event is scheduled to occur. Usage: !when <event>')
async def when(ctx, eventname):
    if eventname in eventlist.keys():
        timestmp = eventlist[eventname]['time']
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
    command_guild = ctx.guild

    logger.info(command_guild)

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
        eventlist[eventname].update(timeentry)
        save(eventlist)

        #eventlist[event].update(timeentry)
    elif command == 'who':
        eventlist[eventname]['who'] = []
        wholist = eventlist[eventname]['who']
        if content[0] == 'everyone':
            wholist.append('@everyone')
        else:
            for index, item in enumerate(content):
                user = str(discord.utils.get(guild.members, name=item))
                userTuple = (item, user)
                wholist.append(userTuple)
        save(eventlist)

    elif command == "auto":
        if len(content)>1:
            response = "Error: 'auto' only takes one argument: yes or no"
            await ctx.send(response)
        else:
            if content[0].lower() == 'yes':
                eventlist[eventname]['auto'] = True
            elif content[0].lower() == 'no':
                eventlist[eventname]['auto'] = False
            else:
                response = "Error: argument for 'auto' must be either 'yes' or 'no'"
                await ctx.send(response)
            save(eventlist)


    response = f'{command} for {eventname} set!'
    await ctx.send(response)

@bot.command(name='who', help="Enter an event's name to see who's attending Usage: !who <event>")
async def getWho(ctx, eventname=None):
    who = eventlist[eventname]['who']
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
    if eventname is None:
        response = "You must supply an event to remind people of!"
        await ctx.send(response)
    else:
        who = eventlist[eventname]['who']
        timestamp = eventlist[eventname]['time']
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
    print('Running loop')
    now = datetime.now()
    now_timestamp = datetime.timestamp(now)

    #These will need to be changed if bot is used on multiple servers
    channel = bot.get_channel(872282820314292235)
    guild = bot.get_guild(872282470396080208)

    for eventname in eventlist:
        if eventlist[eventname]['auto'] == True:
            stored_timestamp = int(eventlist[eventname]['time'])
            if (stored_timestamp - now_timestamp < 86400) and (now.hour == 12):
                who = eventlist[eventname]['who']

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
