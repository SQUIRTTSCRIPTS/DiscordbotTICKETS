import os
import discord
from discord.ext import commands
from discord.ui import View, Button

# -----------------------
# Load Environment Variables
# -----------------------
TOKEN = os.getenv("TOKEN")
GUILD_ID = os.getenv("GUILD_ID")
STAFF_ROLE_ID = os.getenv("STAFF_ROLE_ID")
TICKET_CATEGORY_ID = os.getenv("TICKET_CATEGORY_ID")
TICKET_LOG_CHANNEL_ID = os.getenv("TICKET_LOG_CHANNEL_ID")

# Validate Secrets
if not all([TOKEN, GUILD_ID, STAFF_ROLE_ID, TICKET_CATEGORY_ID, TICKET_LOG_CHANNEL_ID]):
    raise ValueError("🚫 Missing one or more environment variables. Check your Replit secrets.")

# Convert IDs to integers
GUILD_ID = int(GUILD_ID)
STAFF_ROLE_ID = int(STAFF_ROLE_ID)
TICKET_CATEGORY_ID = int(TICKET_CATEGORY_ID)
TICKET_LOG_CHANNEL_ID = int(TICKET_LOG_CHANNEL_ID)

# -----------------------
# Initialize Bot
# -----------------------
intents = discord.Intents.default()
intents.guilds = True
intents.members = True
intents.messages = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# -----------------------
# Button Views
# -----------------------
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="🎟 Purchase Ticket", custom_id="purchase_ticket", style=discord.ButtonStyle.green))
        self.add_item(Button(label="🛠 Support Ticket", custom_id="support_ticket", style=discord.ButtonStyle.blurple))

class CloseButton(View):
    def __init__(self):
        super().__init__(timeout=None)
        self.add_item(Button(label="❌ Close Ticket", custom_id="close_ticket", style=discord.ButtonStyle.red))

# -----------------------
# Bot Events
# -----------------------
@bot.event
async def on_ready():
    print(f"✅ Logged in as {bot.user}")
    guild = bot.get_guild(GUILD_ID)

    if not guild:
        print("❗ Guild not found. Check GUILD_ID.")
        return

    ticket_channel = discord.utils.get(guild.text_channels, name="🎫⫸・ticket")
    if not ticket_channel:
        print("❗ Channel '🎫⫸・ticket' not found. Create it in your server.")
        return

    await ticket_channel.purge()

    embed = discord.Embed(
        title="🎫 Create a Ticket",
        description="Click a button below to open a ticket.",
        color=0x5865F2
    )
    await ticket_channel.send(embed=embed, view=TicketView())

@bot.event
async def on_interaction(interaction: discord.Interaction):
    if interaction.type != discord.InteractionType.component:
        return

    custom_id = interaction.data["custom_id"]
    guild = interaction.guild
    user = interaction.user

    if custom_id in ["purchase_ticket", "support_ticket"]:
        ticket_type = "purchase" if custom_id == "purchase_ticket" else "support"
        channel_name = f"{user.name.lower()}-{ticket_type}-ticket"

        existing_channel = discord.utils.get(guild.text_channels, name=channel_name)
        if existing_channel:
            await interaction.response.send_message("❗ You already have an open ticket.", ephemeral=True)
            return

        category = guild.get_channel(TICKET_CATEGORY_ID)
        staff_role = guild.get_role(STAFF_ROLE_ID)

        overwrites = {
            guild.default_role: discord.PermissionOverwrite(view_channel=False),
            user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
            staff_role: discord.PermissionOverwrite(view_channel=True, send_messages=True)
        }

        channel = await guild.create_text_channel(channel_name, category=category, overwrites=overwrites)

        greeting = (
            f"👋 Hello {user.mention}, please provide your payment method or proof of purchase."
            if ticket_type == "purchase"
            else f"👋 Hello {user.mention}, describe your issue and a staff member will assist you shortly."
        )

        await channel.send(content=greeting, view=CloseButton())
        await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

    elif custom_id == "close_ticket":
        channel = interaction.channel
        log_channel = guild.get_channel(TICKET_LOG_CHANNEL_ID)

        if log_channel:
            await log_channel.send(f"🗑 Ticket `{channel.name}` closed by {user.mention}")

        await interaction.response.send_message("✅ Ticket closing...", ephemeral=True)
        await channel.delete()

# -----------------------
# Start Bot
# -----------------------
bot.run(TOKEN)
