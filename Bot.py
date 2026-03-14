import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
import re
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont
import io
from urllib.request import urlopen
import asyncio

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
WELCOME_CHANNEL_ID = int(os.getenv('WELCOME_CHANNEL_ID', '0'))
EMOJI_MESSAGE_URL = os.getenv('EMOJI_MESSAGE_URL', '')

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
intents.guilds = True

bot = commands.Bot(command_prefix="!", intents=intents)
custom_emoji = None

async def extract_emoji_from_url(url):
    try:
        match = re.match(r'https://discord(?:app)?\.com/channels/(\d+)/(\d+)/(\d+)', url)
        if not match:
            return None
        
        guild_id, channel_id, message_id = map(int, match.groups())
        channel = bot.get_channel(channel_id)
        
        if channel is None:
            channel = await bot.fetch_channel(channel_id)
        
        message = await channel.fetch_message(message_id)
        emoji_pattern = r'<(a)?:(\w+):(\d+)>'
        emojis = re.findall(emoji_pattern, message.content)
        
        if emojis:
            animated, name, emoji_id = emojis[0]
            emoji_format = f"<{'a' if animated else ''}:{name}:{emoji_id}>"
            return emoji_format
        
        return None
    except Exception as e:
        print(f"Error extracting emoji: {e}")
        return None

@bot.event
async def on_ready():
    global custom_emoji
    print(f'✅ Bot logged in as {bot.user}')
    print(f'📊 Connected to {len(bot.guilds)} server(s)')
    
    if EMOJI_MESSAGE_URL:
        custom_emoji = await extract_emoji_from_url(EMOJI_MESSAGE_URL)
        if custom_emoji:
            print(f'✅ Loaded custom emoji: {custom_emoji}')
        else:
            custom_emoji = '😊'
    else:
        custom_emoji = '😊'
    
    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="EVE SERVER"
        )
    )

@bot.event
async def on_member_join(member):
    if WELCOME_CHANNEL_ID == 0:
        return
    
    channel = bot.get_channel(WELCOME_CHANNEL_ID)
    if channel:
        embed = discord.Embed(
            title="🎉 Welcome to our server!",
            description=f"welcome to our server ! {member.mention}\n\nby pxn & lno\n\nplease read the rules before chatting chaww 🩵",
            color=discord.Color.blue()
        )
        embed.set_thumbnail(url=member.avatar.url)
        await channel.send(embed=embed)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content == ".":
        response = f"يازين اللي ينقط {custom_emoji}"
        await message.reply(response, mention_author=False)
    
    elif message.content == "بنات":
        await message.reply("هلا عيونهم", mention_author=False)
    
    await bot.process_commands(message)

class TicketOptions(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.select(
        placeholder="اختر نوع التذكرة",
        options=[
            discord.SelectOption(label="طلب عام", value="general", emoji="❓"),
            discord.SelectOption(label="اقتراح", value="suggestion", emoji="📢"),
            discord.SelectOption(label="طلب روم", value="room_request", emoji="💭"),
        ]
    )
    async def ticket_select(self, interaction: discord.Interaction, select: Select):
        option = select.values[0]
        guild = interaction.guild
        category_name = "Tickets"
        
        category = discord.utils.get(guild.categories, name=category_name)
        if not category:
            category = await guild.create_category(category_name)
        
        ticket_name = f"ticket-{interaction.user.name}-{option}"
        channel = await guild.create_text_channel(
            ticket_name,
            category=category,
            topic=f"تذكرة من {interaction.user.mention}"
        )
        
        await channel.set_permissions(interaction.user, view_channel=True, send_messages=True, read_messages=True)
        await channel.set_permissions(guild.default_role, view_channel=False)
        
        embed = discord.Embed(
            title=f"🎟️ تذكرة جديدة - {option}",
            description=f"شكرا لك {interaction.user.mention} على التواصل معنا!\n\nسيقوم الفريق بالرد عليك قريبا ⏳",
            color=discord.Color.green()
        )
        
        close_button = Button(label="إغلاق التذكرة", style=discord.ButtonStyle.red, emoji="🔐")
        close_view = View()
        close_view.add_item(close_button)
        
        async def close_ticket(button_interaction: discord.Interaction):
            if button_interaction.user.id == interaction.user.id:
                await channel.delete()
                await button_interaction.response.defer()
        
        close_button.callback = close_ticket
        await channel.send(embed=embed, view=close_view)
        
        await interaction.response.send_message(
            f"✅ تم إنشاء التذكرة: {channel.mention}",
            ephemeral=True
        )

@bot.command(name='ticket')
async def ticket(ctx):
    is_owner = ctx.author.id == ctx.guild.owner_id
    if not is_owner:
        await ctx.send("❌ ليس لديك صلاحية", delete_after=5)
        return
    
    embed = discord.Embed(
        title="🎟️ نظام التذاكر",
        description="اختر نوع التذكرة أدناه:",
        color=discord.Color.purple()
    )
    
    view = TicketOptions()
    await ctx.send(embed=embed, view=view)

@bot.command(name='status')
async def status(ctx, *, text):
    is_owner = ctx.author.id == ctx.guild.owner_id
    if not is_owner:
        await ctx.send("❌ ليس لديك صلاحية", delete_after=5)
        return
    
    await bot.change_presence(
        activity=discord.Activity(type=discord.ActivityType.watching, name=text)
    )
    await ctx.send(f"✅ تم تحديث الحالة إلى: {text}")

bot.run(TOKEN)
