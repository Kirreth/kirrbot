# -*- coding: iso-8859-1 -*-
import random
import sqlite3
import asyncio
import discord
from discord.ext import commands
from datetime import datetime
from googleapiclient.discovery import build
import requests
import re
import os


verbindung = sqlite3.connect("videos.db")
zeiger = verbindung.cursor()
zeiger.execute("CREATE TABLE IF NOT EXISTS videos(link VARCHAR(50))")
verbindung.commit()

# YouTube Data API Schlüssel
api_key = "API-KEY"

# YouTube Kanal ID
channel_id = "KANAL-ID"

# Kanal-ID, in dem die Nachricht gepostet werden soll
discord_channel_id = 'CHANNEL-ID'

# YouTube API Verbindung herstellen
youtube = build('youtube', 'v3', developerKey=api_key)

# Intent mit message_content hinzufügen
intents = discord.Intents.all()
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("Bot is Up and Ready!")
    try:
        synced = await bot.tree.sync()
        print(f"Synced {len(synced)} command(s)")
    except Exception as e:
        print(e)
        
    await check_youtube_channel()

@bot.event
async def on_message(msg):
    if msg.author.id == bot.user.id:
        return

    msg_content = msg.content.lower()
    curse_words = ['discord.com/invite']
    
    # delete curse word if match with the list
    if any(word in msg_content for word in curse_words):
        await msg.delete()

    # Befehlsverarbeitung zulassen
    await bot.process_commands(msg)

# Funktion zum Überprüfen des YouTube-Kanals auf neue Videos
async def check_youtube_channel():
    while True:
        response = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            maxResults=1,  # Anzahl der Videos, die abgerufen werden sollen
            order='date',
            type='video'# Sortierung nach Datum
        ).execute()

        for item in response['items']:
            video_id = item['id']['videoId']
            video_title = item['snippet']['title']
            video_link = f"https://www.youtube.com/watch?v={video_id}"

            # Überprüfen, ob das Video bereits in der Datenbank ist
            zeiger.execute("SELECT link FROM videos WHERE link = ?", (video_link,))
            result = zeiger.fetchone()

            if result is None:  # Video ist noch nicht in der Datenbank
                # Abrufen der Details zum Video, einschließlich der Dauer
                video_response = youtube.videos().list(
                    part='contentDetails',
                    id=video_id
                ).execute()

                # Extrahieren der Dauer des Videos
                duration = video_response['items'][0]['contentDetails']['duration']
                duration = duration[2:]  # Entferne das 'PT'-Präfix
                minutes = 0
    
                if 'H' in duration:
                    hours, duration = duration.split('H')
                    minutes += int(hours) * 60
    
                if 'M' in duration:
                    minutes_part = duration.split('M')[0]
                    minutes += int(minutes_part)
                
                if minutes >= 2:
                    message = f"Hey @everyone **Niklas Steenfatt** hat gerade ein neues Video gepostet. Schau es dir bis zum Schluss an und hinterlasse einen netten Kommentar. \n[{video_title}]({video_link})"
                    
                    # Video-Link in der Datenbank speichern
                    zeiger.execute("INSERT INTO videos (link) VALUES (?)", (video_link,))
                    verbindung.commit()

                    # Nachricht an Discord senden
                    await post_to_discord(message)

        # Warte 60 Sekunden, bevor der Kanal erneut überprüft wird
        await asyncio.sleep(900)

# Funktion zum Posten einer Nachricht in einem Discord-Kanal
async def post_to_discord(message):
    channel = bot.get_channel(int(discord_channel_id))
    await channel.send(message)    
    


# Bot starten
bot.run(os.getenv('TOKEN'))
