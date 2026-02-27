import discord
from discord.ext import commands
from discord import app_commands
import json, os, sqlite3, random
from typing import Optional

# ================= CONFIG =================
TOKEN = os.getenv("DISCORD_TOKEN")

if not TOKEN:
    raise ValueError("No DISCORD_TOKEN found in environment variables.")

# ---------- TICKET ROLE IDS ----------
CEO_ROLE_ID = 1393269068689309746
CAO_ROLE_ID = 1393269824544575498
CMO_ROLE_ID = 1421109822526591077
RECRUITER_ROLE_ID = 1393270492429025370
MOD_ROLE_ID = 1468120470304981194

# ================= INTENTS =================
intents = discord.Intents.default()
intents.members = True
intents.message_content = True

bot = commands.Bot(command_prefix="!", intents=intents)

# ================= DATABASE =================
db = sqlite3.connect("events.db")
cursor = db.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS scheduled_events (
    event_id TEXT PRIMARY KEY,
    date TEXT,
    dep_airport TEXT,
    arr_airport TEXT,
    dep_time TEXT,
    flight_time TEXT,
    operator TEXT,
    flight_no TEXT,
    aircraft TEXT,
    server TEXT
)
""")
db.commit()

# ================= GATE DATA =================
DATA_FILE = "gate_sessions.json"

if not os.path.exists(DATA_FILE):
    with open(DATA_FILE, "w") as f:
        json.dump({}, f)

with open(DATA_FILE, "r") as f:
    gate_sessions = json.load(f)

def save_gate_sessions():
    with open(DATA_FILE, "w") as f:
        json.dump(gate_sessions, f, indent=4)

def generate_event_id():
    return f"OAV-{random.randint(100, 9999)}"

def parse_color(hex_color: Optional[str]):
    if not hex_color:
        return 0xb5985a
    try:
        return int(hex_color.replace("#", ""), 16)
    except:
        return 0xb5985a

# ================= TICKET SYSTEM =================
class TicketPanel(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="🛠 Staff Help Ticket", style=discord.ButtonStyle.primary, custom_id="ticket_staff")
    async def staff(self, interaction: discord.Interaction, _):
        await create_ticket(interaction, "staff-help", [MOD_ROLE_ID])

    @discord.ui.button(label="🧑‍✈️ Recruiter Ticket", style=discord.ButtonStyle.success, custom_id="ticket_recruiter")
    async def recruiter(self, interaction: discord.Interaction, _):
        await create_ticket(interaction, "recruiter", [RECRUITER_ROLE_ID, CFI_ROLE_ID])

    @discord.ui.button(label="🎮 Career Mode Ticket", style=discord.ButtonStyle.secondary, custom_id="ticket_career")
    async def career(self, interaction: discord.Interaction, _):
        await create_ticket(interaction, "career-mode", [CEO_ROLE_ID, CAO_ROLE_ID])

async def create_ticket(interaction, name, role_ids):
    guild = interaction.guild
    category = discord.utils.get(guild.categories, name="TICKETS")

    if not category:
        category = await guild.create_category("TICKETS")

    overwrites = {
        guild.default_role: discord.PermissionOverwrite(view_channel=False),
        interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True),
        guild.me: discord.PermissionOverwrite(view_channel=True)
    }

    pings = []
    for rid in role_ids:
        role = guild.get_role(rid)
        if role:
            overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True)
            pings.append(role.mention)

    channel = await guild.create_text_channel(
        name=f"{name}-{interaction.user.name}",
        category=category,
        overwrites=overwrites
    )

    embed = discord.Embed(
        title="🎫 Ticket Opened",
        description=f"Opened by {interaction.user.mention}",
        color=0x2f3136
    )

    await channel.send(content=" ".join(pings), embed=embed)
    await interaction.response.send_message(f"✅ Ticket created: {channel.mention}", ephemeral=True)

# ================= EVENTS =================
@bot.tree.command(name="addevent")
async def addevent(
    interaction: discord.Interaction,
    date: str,
    dep_airport: str,
    arr_airport: str,
    dep_time: str,
    flight_time: str,
    operator: str,
    flight_no: str,
    aircraft: str,
    server: str
):
    eid = generate_event_id()

    cursor.execute("""
    INSERT INTO scheduled_events VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (eid, date, dep_airport, arr_airport, dep_time, flight_time,
          operator, flight_no, aircraft, server))
    db.commit()

    await interaction.response.send_message(
        f"✅ Event saved\n📌 ID: `{eid}`", ephemeral=True
    )

# (Rest of your event embed + sendembed stays same — trimmed here for space)

# ================= READY =================
@bot.event
async def on_ready():
    await bot.tree.sync()
    bot.add_view(TicketPanel())
    print(f"✅ Logged in as {bot.user}")

bot.run(TOKEN)
