# -*- coding: utf-8 -*-

import discord
from googleapiclient.discovery import build
import asyncio
import sqlite3

# Datenbank-Verbindung
verbindung = sqlite3.connect("videos.db")
zeiger = verbindung.cursor()
zeiger.execute("CREATE TABLE IF NOT EXISTS videos(link VARCHAR(50))")
verbindung.commit()

# YouTube Data API Schlüssel
api_key = "KEY"

# YouTube Kanal ID
channel_id = "Kanal-ID"

# Discord Bot Token
discord_token = "TOKEN"

# Kanal-ID, in dem die Nachricht gepostet werden soll
discord_channel_id = "Discord-Channel-ID"

# Verbindung zum Discord-Client herstellen
client = discord.Client(intents=discord.Intents.all())

# YouTube API Verbindung herstellen
youtube = build('youtube', 'v3', developerKey=api_key)

@client.event
async def on_ready():
    print(f'Eingeloggt als {client.user}')
    await check_youtube_channel()

# Funktion zum Überprüfen des YouTube-Kanals auf neue Videos
async def check_youtube_channel():
    while True:
        response = youtube.search().list(
            part='snippet',
            channelId=channel_id,
            maxResults=1,  # Anzahl der Videos, die abgerufen werden sollen
            order='date'   # Sortierung nach Datum
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
                    message = f"Hey @everyone **Niklas Steenfatt** hat gerade ein neues Video gepostet. Schau es dir bis zum Schluss an und hinterlasse einen netten Kommentar. 🙌 \n[{video_title}]({video_link})"
                    
                    # Video-Link in der Datenbank speichern
                    zeiger.execute("INSERT INTO videos (link) VALUES (?)", (video_link,))
                    verbindung.commit()

                    # Nachricht an Discord senden
                    await post_to_discord(message)

        # Warte 60 Sekunden, bevor der Kanal erneut überprüft wird
        await asyncio.sleep(60)

# Funktion zum Posten einer Nachricht in einem Discord-Kanal
async def post_to_discord(message):
    channel = client.get_channel(int(discord_channel_id))
    await channel.send(message)

client.run(discord_token)
