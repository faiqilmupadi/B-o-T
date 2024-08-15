import discord
import requests
import asyncio

intents = discord.Intents.default()
intents.messages = True
intents.guilds = True

client = discord.Client(intents=intents)
stop_threads = {}

API_URL = 'http://flask_app:5000/'

#yang ini aman
async def add_user(name, username, interval):
    response = requests.post(f'{API_URL}/add_user', json={'name': name, 'username': username, 'interval': interval})
    return response.status_code

#yang ini kaga aman (cacat)
async def add_task(username, description, deadline):
    data = {'username': username, 'description': description, 'deadline': deadline}
    response = requests.post(f'{API_URL}/add_task', json=data)
    print(f'Response from server: {response.text}')
    return response.status_code

#yang ini aman
async def complete_task(task_id):
    response = requests.post(f'{API_URL}/complete_task', json={'task_id': task_id})
    return response.status_code

#yang ini kaga aman (cacat)
async def get_user_tasks(username):
    response = requests.get(f'{API_URL}/get_tasks/{username}')
    return response.json() if response.status_code == 200 else []

#yang ini kaga aman (cacat)
async def get_overdue_tasks(username):
    response = requests.get(f'{API_URL}/get_overdue_tasks/{username}')
    return response.json() if response.status_code == 200 else []

#yang ini blm dicek
async def send_reminder(username, interval):
    while True:
        tasks = await get_user_tasks(username)
        if tasks:
            task_list = "\n".join([f"- {task['description']} (Deadline: {task['deadline']})" for task in tasks])
            channel = discord.utils.get(client.get_all_channels(), name='general')
            await channel.send(f"Reminder for {username}:\n{task_list}")
        await asyncio.sleep(interval * 24 * 3600)  
@client.event
async def on_ready():
    print(f'We have logged in as {client.user}')

@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if message.content.startswith('!add_user'):
        _, name, username, interval = message.content.split()
        interval = int(interval)
        status_code = await add_user(name, username, interval)
        await message.channel.send('Ini buat ngecek')
        if status_code == 201:
            if username not in stop_threads:
                stop_threads[username] = asyncio.create_task(send_reminder(username, interval))
            await message.channel.send('User added successfully!')
        else:
            await message.channel.send('Failed to add user!')

    elif message.content.startswith('!add_task'):
        _, username, description, deadline = message.content.split(maxsplit=3)
        status_code = await add_task(username, description, deadline)
        await message.channel.send('Ini buat ngecek')
        if status_code == 201:
            await message.channel.send('Task added successfully!')
        else:
            await message.channel.send('Failed to add task!')

    elif message.content.startswith('!complete_task'):
        _, task_id = message.content.split()
        status_code = await complete_task(task_id)
        await message.channel.send('Ini buat ngecek')
        if status_code == 200:
            await message.channel.send('Task marked as completed!')
        else:
            await message.channel.send('Failed to complete task!')

    elif message.content.startswith('!delete_task'):
        _, task_id = message.content.split()
        status_code = await delete_task(task_id)
        await message.channel.send('Ini buat ngecek')
        if status_code == 200:
            await message.channel.send('Task deleted successfully!')
        else:
            await message.channel.send('Failed to delete task!')

    elif message.content.startswith('!list_tasks'):
        _, username = message.content.split()
        user_tasks = await get_user_tasks(username)
        await message.channel.send('Ini buat ngecek')
        if user_tasks:
            tasks_list = "\n".join([f"{i+1}. {task['description']} - {'udah' if task['completed'] else 'belom'}" for i, task in enumerate(user_tasks)])
            await message.channel.send(f"**Daftar Tugas untuk {username}**:\n{tasks_list}")
        else:
            await message.channel.send('No tasks found!')

    elif message.content.startswith('!check_overdue'):
        _, username = message.content.split()
        overdue_tasks = await get_overdue_tasks(username)
        await message.channel.send('Ini buat ngecek')
        if overdue_tasks:
            tasks_list = "\n".join([f"{i+1}. {task['description']} - {task['deadline']}" for i, task in enumerate(overdue_tasks)])
            await message.channel.send(f"**Tugas Terlambat untuk {username}**:\n{tasks_list}")
        else:
            await message.channel.send('No overdue tasks!')

    elif message.content.startswith('!hello'):
        await message.channel.send('Hello!')


client.run('MTI0NzE3NDIxNDU0MTM3NzY5MQ.GhVXcr.WUqm_YfS6DYvSYw3pizwujoI7Jecx4mE6rvCCU')
