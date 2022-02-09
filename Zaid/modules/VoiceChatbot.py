# @lyciachatbot support Now
import os
import aiofiles
import aiohttp
from random import randint
from pyrogram import filters
from Zaid import pbot as LOVELY

async def fetch(url):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            try:
                data = await resp.json()
            except:
                data = await resp.text()
    return data

async def ai_lovely(url):
    ai_name = "Lovely.mp3"
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status == 200:
                f = await aiofiles.open(ai_name, mode="wb")
                await f.write(await resp.read())
                await f.close()
    return ai_name


@LOVELY.on_message(filters.command("Lovely"))
async def Lovely(_, message):
    if len(message.command) < 2:
        await message.reply_text("Lovely AI Voice Chatbot")
        return
    text = message.text.split(None, 1)[1]
    lovely = text.replace(" ", "%20")
    m = await message.reply_text("Lovely Is Best...")
    try:
        L = await fetch(f"https://api.affiliateplus.xyz/api/chatbot?message={lycia}&botname=lovely&ownername=Tushar204&user=1")
        chatbot = L["message"]
        VoiceAi = f"https://lyciavoice.herokuapp.com/lycia?text={chatbot}&lang=hi"
        name = "lovely"
    except Exception as e:
        await m.edit(str(e))
        return
    await m.edit("Made By @Tushar204...")
    LovelyVoice = await ai_lovely(VoiceAi)
    await m.edit("Repyping...")
    await message.reply_audio(audio=LovelyVoice, title=chatbot, performer=name)
    os.remove(LovelyVoice)
    await m.delete()
