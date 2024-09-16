import discord
from discord.ext import commands, tasks
from discord import app_commands
import json
import logging
from datetime import datetime
import random 

# Laad configuratie
with open("config.json") as f:
    config = json.load(f)

# Verkrijg instellingen uit configuratie
bot_token = config["general"]["bot-token"]
guild_id = int(config["general"]["guild_id"])
logging_channel_id = int(config["general"].get("logging_channel_id", 0))
approved_user_ids = config["general"].get("approved_user_ids", [])

launch_time = datetime.now()

# Waarschuwingen opslaan in een dictionary {member_id: [list_of_warnings]}
warnings = {}

# Stel de logger in
logging.basicConfig(
    filename='bot_warnings.log',  # Het bestand waarin de waarschuwingen worden gelogd
    level=logging.INFO,  # Log-niveau
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

class Example(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.status_loop.start()  # Start de dynamische Rich Presence loop

    example = app_commands.Group(name="nigga", description="Example")

    @example.command(name="test", description="test")
    async def test(self, interaction: discord.Interaction):
        await interaction.response.send_message("Kanker hoer waarom heb je me wakker gemaakt")

    @example.command(name="ping", description="pong")
    async def ping(self, interaction: discord.Interaction):
        latency = round(self.client.latency * 1000)  # Convert to milliseconds
        time = f"<t:{int(launch_time.timestamp())}:R>"

        embed = discord.Embed(title='Ping and Uptime', color=discord.Color.green())
        embed.add_field(name='Latency', value=f'{latency}ms', inline=False)
        embed.add_field(name='Uptime', value=time, inline=False)

        await interaction.response.send_message(embed=embed)


    @example.command(name="8ball", description="Krijg een willekeurig antwoord op een vraag.")
    async def eight_ball(self, interaction: discord.Interaction, question: str):
        responses = [
            "Ja", "Nee", "Misschien", "Probeer later opnieuw", "Zeker weten",
            "Ik zou er niet op rekenen", "Het is twijfelachtig", "Houd je kanker bek kanker hoer"
        ]
        response = random.choice(responses)
        await interaction.response.send_message(f"Vraag: {question}\nAntwoord: {response}")

    # aankondiging maken. (Admin only)
    @example.command(name="announce", description="Make an announcement.")
    async def announce(self, interaction: discord.Interaction, *, message: str):
        if interaction.user.id not in approved_user_ids:
            await interaction.response.send_message("Jij mag niet praten neef je hebt niet genoeg rechten.")
            return
        
        announcement = f"@everyone , Kijk alsjeblieft even naar het volgende bericht: {message}"
        await interaction.channel.send(announcement)
        await interaction.response.send_message("Aankondiging verzonden.", ephemeral=True)

        logging.info(f"aankondiging verzonden door: {interaction.user}: {message}")

        if logging_channel_id:
            log_channel = self.client.get_channel(logging_channel_id)
            if log_channel:
                log_embed = discord.Embed(
                    title="Aankonding verzonden",
                    description=f"Aankondiging verzonden door {interaction.user.mention}: {message}",
                    color=discord.Color.blue()
                )
                await log_channel.send(embed=log_embed)

         # Lockdown commando (alleen voor goedgekeurde gebruikers)
    @example.command(name="lockdown", description="Sluit een tekstkanaal of alle kanalen af.")
    async def lockdown(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if interaction.user.id not in approved_user_ids:
            await interaction.response.send_message("Je hebt niet genoeg rechten om deze command uit te voeren.")
            return

        if channel is None:
            # Als geen kanaal is opgegeven, sluit dan alle tekstkanalen af
            channels = interaction.guild.text_channels
            await interaction.response.send_message(f"Alle kanalen worden afgesloten door {interaction.user.mention}.")

            for ch in channels:
                # Update permissies voor elk kanaal
                await ch.set_permissions(interaction.guild.default_role, send_messages=False)
                logging.info(f"Channel {ch.name} afgesloten door {interaction.user}")
            await interaction.followup.send("Alle tekstkanalen zijn afgesloten.")
        else:
            # Alleen het opgegeven kanaal afsluiten
            await channel.set_permissions(interaction.guild.default_role, send_messages=False)
            await interaction.response.send_message(f"Channel {channel.mention} is afgesloten door {interaction.user.mention}.")
            logging.info(f"Channel {channel.name} afgesloten door {interaction.user}")

    # Unlock commando (alleen voor goedgekeurde gebruikers)
    @example.command(name="unlock", description="Heropent een tekstkanaal of alle kanalen.")
    async def unlock(self, interaction: discord.Interaction, channel: discord.TextChannel = None):
        if interaction.user.id not in approved_user_ids:
            await interaction.response.send_message("Je hebt niet genoeg rechten om deze command uit te voeren.")
            return

        if channel is None:
            # Als geen kanaal is opgegeven, open dan alle tekstkanalen
            channels = interaction.guild.text_channels
            await interaction.response.send_message(f"Alle kanalen worden heropend door {interaction.user.mention}.")

            for ch in channels:
                # Herstel permissies voor elk kanaal
                await ch.set_permissions(interaction.guild.default_role, send_messages=True)
                logging.info(f"Channel {ch.name} heropend door {interaction.user}")
            await interaction.followup.send("Alle tekstkanalen zijn heropend.")
        else:
            # Alleen het opgegeven kanaal heropenen
            await channel.set_permissions(interaction.guild.default_role, send_messages=True)
            await interaction.response.send_message(f"Channel {channel.mention} is heropend door {interaction.user.mention}.")
            logging.info(f"Channel {channel.name} heropend door {interaction.user}")


    # Waarschuw commando (alleen voor goedgekeurde gebruikers)
    @example.command(name="warn", description="Send a warning message")
    async def warn(self, interaction: discord.Interaction, member: discord.Member, *, reason: str):
        if interaction.user.id not in approved_user_ids:
            await interaction.response.send_message("jij hebt niet genoeg rechten om deze neger te warnen.")
            return

        if member.id not in warnings:
            warnings[member.id] = []
        warnings[member.id].append(reason)

        embed = discord.Embed(
            title="Nigga got warned.",
            description=f"{member.mention} is gewarned",
            color=discord.Color.orange()
        )
        embed.add_field(name="Reason", value=reason, inline=False)

        logging.info(f"Warning issued by {interaction.user} to {member} for: {reason}")

        await interaction.response.send_message(embed=embed)

        if logging_channel_id:
            log_channel = self.client.get_channel(logging_channel_id)
            if log_channel:
                await log_channel.send(embed=embed)

    # Kick (alleen voor goedgekeurde gebruikers)
    @example.command(name="kick", description="Kick a member from the server")
    async def kick(self, interaction: discord.Interaction, member: discord.Member, *, reason: str):
        if interaction.user.id not in approved_user_ids:
            await interaction.response.send_message("jij hebt niet genoeg rechten om deze neger te kicken.")
            return

        try:
            await member.kick(reason=reason)
            embed = discord.Embed(
                title="Member Kicked",
                description=f"{member.mention} HAHAHAHA JE BENT GEKICKED.",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)

            logging.info(f"Member kicked by {interaction.user} from {member} for: {reason}")

            await interaction.response.send_message(embed=embed)

            if logging_channel_id:
                log_channel = self.client.get_channel(logging_channel_id)
                if log_channel:
                    await log_channel.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("Ik kan deze bledder niet kicken man sorry")
        except Exception as e:
            await interaction.response.send_message(f"An error occurred: {e}")

    # Server-mute ( vc )
    @example.command(name="mute", description="Server-mute a member in a voice channel")
    async def mute(self, interaction: discord.Interaction, member: discord.Member, *, reason: str):
        if interaction.user.id not in approved_user_ids:
            await interaction.response.send_message("Je hebt niet genoeg rechten.")
            return

        if not member.voice:  # Controleer of het lid in een voice channel zit
            await interaction.response.send_message(f"{member.mention} is not in a voice channel.")
            return

        try:
            await member.edit(mute=True, reason=reason)
            embed = discord.Embed(
                title="Member Muted",
                description=f"{member.mention} HAHAHAHHA je kan niet meer praten kanker sukkel",
                color=discord.Color.red()
            )
            embed.add_field(name="Reason", value=reason, inline=False)

            logging.info(f"Member muted by {interaction.user} in voice channel for: {reason}")

            await interaction.response.send_message(embed=embed)

            if logging_channel_id:
                log_channel = self.client.get_channel(logging_channel_id)
                if log_channel:
                    await log_channel.send(embed=embed)
        except discord.Forbidden:
            await interaction.response.send_message("Ik kan deze persoon niet muten sorry man.")
        except Exception as e:
            await interaction.response.send_message(f"Stuk gegaan: {e}")

    # Check warn
    @example.command(name="listwarns", description="List all warnings for a user")
    async def listwarns(self, interaction: discord.Interaction, member: discord.Member):
        if interaction.user.id not in approved_user_ids:
            await interaction.response.send_message("Je hebt niet genoeg rechten, kanker slaaf")
            return

        if member.id in warnings and warnings[member.id]:
            embed = discord.Embed(
                title=f"Warnings for {member}",
                color=discord.Color.orange()
            )
            for i, warn in enumerate(warnings[member.id], 1):
                embed.add_field(name=f"Warning {i}", value=warn, inline=False)
        else:
            embed = discord.Embed(
                title="No Warnings",
                description=f"{member.mention} Heeft geen warns.",
                color=discord.Color.green()
            )

        await interaction.response.send_message(embed=embed)

    # Clear command
    @example.command(name="clear", description="Clear a number of messages from the chat")
    async def clear(self, interaction: discord.Interaction, amount: int):
        if interaction.user.id not in approved_user_ids:
            await interaction.response.send_message("Je hebt niet genoeg rechten om deze command uit te voeren.")
            return

        if amount <= 0:
            await interaction.response.send_message("Please specify a number greater than 0.")
            return

        try:
            # Verwijder berichten
            deleted = await interaction.channel.purge(limit=amount)
            await interaction.channel.send(f"Successfully deleted {len(deleted)} messages.")
            
            # Logs voor het clearen van berichten
            logging.info(f"{interaction.user} cleared {len(deleted)} messages in {interaction.channel.name}.")
            
            if logging_channel_id:
                log_channel = self.client.get_channel(logging_channel_id)
                if log_channel:
                    log_embed = discord.Embed(
                        title="Messages Cleared",
                        description=f"{interaction.user.mention} cleared {len(deleted)} messages in {interaction.channel.mention}.",
                        color=discord.Color.blue()
                    )
                    await log_channel.send(embed=log_embed)
        except discord.Forbidden:
            await interaction.response.send_message("Ik heb niet genoeg rechten om deze berichten te verwijderen.")
        except Exception as e:
            await interaction.response.send_message(f"Stuk gegaan: {e}")

    # Rich Presence
    @tasks.loop(minutes=2)  # Deze loop wordt elke 2 minuten uitgevoerd
    async def status_loop(self):
        # Maak een lijst met verschillende activiteiten
        statuses = [
            discord.Activity(type=discord.ActivityType.playing, name="Valorant"),
            discord.Activity(type=discord.ActivityType.watching, name="Kinderporno"),
            discord.Activity(type=discord.ActivityType.listening, name="Burning Down - Dual Damage"),
            discord.Activity(type=discord.ActivityType.playing, name="Met zichzelf")
        ]
        
        # Kies willekeurig een activiteit uit de lijst
        new_status = random.choice(statuses)
        
        # Update de Rich Presence van de bot
        await self.client.change_presence(activity=new_status)

    @status_loop.before_loop
    async def before_status_loop(self):
        await self.client.wait_until_ready()  # Wacht tot de bot volledig is opgestart
        
    @commands.Cog.listener()
    async def on_ready(self):
        print("Bot is opgestart, kanker zooi moet ik weer aan het werk")

        # Zoek het "general" kanaal
        general_channel = discord.utils.get(self.client.get_all_channels(), name="general")
        
        if general_channel:
            try:
                await general_channel.send("@everyone Hey pookies")
                logging.info(f"Bericht gestuurd in {general_channel.name}: 'Hey pookies'")
            except discord.Forbidden:
                logging.error(f"Geen toestemming om berichten te versturen in {general_channel.name}.")
            except Exception as e:
                logging.error(f"Er ging iets mis bij het versturen van het bericht in {general_channel.name}: {e}")
        else:
            logging.error("Geen 'general' kanaal gevonden.")


# Setup de bot
async def setup(client: commands.Bot) -> None:
    await client.add_cog(Example(client))
