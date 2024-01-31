# ------AtlantaVR bot------ #
#   By : helias5605
# ------------------------- #

import random
import discord
import os
import json
import asyncio
import time
from datetime import datetime
from discord import app_commands
from discord.ext import commands
from discord.ui import View, Button
from function_sys import *
from db_handler import *

with open("./data.json", "r") as f:
    data = json.load(f)

version = data['version']
server = str(data['server'])
passed = False
client = commands.Bot(command_prefix='$', intents=discord.Intents.all(), help_command=None)


class ConfirmView(discord.ui.View):
    def __init__(self, ctx, cur, conn, id, date, roles, name):
        super().__init__()
        self.ctx = ctx
        self.cur = cur
        self.conn = conn
        self.id = id
        self.date = date
        self.roles = roles
        self.name = name

    @discord.ui.button(label='Confirmer', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message("🔄 Ajout de l'événement en cours...", ephemeral=True)
        await enregistrer_evenement(self.cur, self.conn, str(self.ctx.message.author), self.id, self.date, self.roles, self.name)
        await asyncio.sleep(2)
        await interaction.edit_original_response(content="**✅ L'événement a été ajouté avec succès"
                                                         " à la base de données.**", view=None)

    @discord.ui.button(label='Annuler', style=discord.ButtonStyle.danger)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message(content="L'ajout de l'événement a été annulé.", view=None)


@client.command(name='add')
@commands.has_permissions(administrator=True)
async def add(ctx: commands.Context, name: str, rôles: str, date: str):
    try:
        role_list = rôles.split(", ")
        id = int(time.time())
        if len(role_list) > 25:
            await ctx.send("Désolé le nombre de rôles à créer est trop élevé pour Discord !\n"
                           "Le maximum est de 25 rôles !")
            await asyncio.sleep(4)
            await ctx.message.delete()
        else:
            cur, conn = await initialiser_db()
            view = ConfirmView(ctx, cur, conn, id, date, rôles, name)
            embed = discord.Embed(title="☑️ Confirmation de l'event...",
                                  description=f"**Nom de l'event:**\n{name}\n**Liste des Rôles:**\n{rôles}\n**Date:**\n{date}",
                                  color=discord.Color.blue())
            embed.set_footer(text=f"Demande d'ajout par {ctx.message.author}")
            await ctx.send("Voulez-vous confirmer l'ajout de cet événement ?", embed=embed, view=view)
    except Exception as e:
        await ctx.send(f"Une erreur est survenue lors de l'ajout de l'événement à la base de données : {e}")
        await asyncio.sleep(4)
        await ctx.message.delete()


@client.tree.command(name='lancer', description='Faire un lancer de dés aléatoire')
async def lancer(interaction: discord.Interaction):
    result = random.randint(1, 6)
    await interaction.response.defer(ephemeral=False)
    await interaction.followup.send(f'{result} 🎲 !')


@client.tree.command(name='help', description='Afficher le menu d\'aide')
async def help(interaction: discord.Interaction):
    embed = discord.Embed(title="Menu d'aide - AtlantaVR", color=discord.Color.blue())
    embed.add_field(name="🎨 Amusement", value="🎲 **/lancer**: Faire un lancer de dés aléatoire\n"
                                              "🧷 **/ping**: Ping le notre bot !", inline=False)
    embed.add_field(name="🎟️ Events", value="🔦 **/events**: Afficher les événement en cours\n"
                                            "ℹ️ **/event_info**: Information détailés d'un event", inline=False)
    embed.set_footer(text=f"Demandé par {interaction.user}")
    # embed.set_image(url="https://cdn.discordapp.com/attachments/1118913269776793670/1199095326787764355/"
    #                     "banniere_discord.png?ex=65ca860c&is=65b8110c&hm=352d1d2e87ccb52ca02a4fda942c0fb5"
    #                     "549bdcff1c6fa2a71472363f141a3717&")
    await interaction.response.send_message(embed=embed, ephemeral=False)


@client.command(name='purge')
@commands.has_permissions(administrator=True)
async def purge(ctx):
    try:
        cur, conn = await initialiser_db()
        await purge_events(cur, conn)
        await ctx.send("Tous les événements ont été purgés de la base de données.")
    except Exception as e:
        await ctx.send(f"Une erreur est survenue lors de la purge des événements : {e}")


@client.tree.command(name='event_info', description='Afficher les détails d\'un événement')
@app_commands.describe(id="Le ID de l'événement")
async def events_info(interaction: discord.Interaction, id: int):
    try:
        nb = 0
        stock = None
        evenement = await display_db()
        if evenement is not None and isinstance(evenement, list):
            while nb < len(evenement) - 1:
                if evenement[nb][0] == id:
                    break
                nb += 1
        if nb != 0:
            embed = discord.Embed(title=f"Événement {evenement[nb][1]} du {evenement[nb][2]}", color=discord.Color.blue())
            for i in range(len(evenement[nb][4].split(", "))):
                if random.randint(0, 1) == 0:
                    stock = f"✅ Disponible - USERNAME"
                else:
                    stock = f"❌ Indisponible - USERNAME"
                embed.add_field(
                    name=f"Rôle {i + 1} - {evenement[nb][4].split(', ')[i]}",
                    value=stock,
                    inline=False
                )
            embed.set_footer(text=f"Créé par {evenement[nb][3]} - ID : {evenement[nb][0]}")
            # embed.set_image(url="https://cdn.discordapp.com/attachments/1118913269776793670/1199095326787764355/"
            #                     "banniere_discord.png?ex=65ca860c&is=65b8110c&hm=352d1d2e87ccb52ca02a4fda942c0fb5"
            #                     "549bdcff1c6fa2a71472363f141a3717&")
            await interaction.response.send_message(embed=embed, ephemeral=False)
        else:
            await interaction.response.send_message("ID non trouvé dans les events en cours", ephemeral=False)
    except Exception as e:
        await interaction.response.send_message(f"Une erreur inattendue est survenue : {e}\n"
                                                "Merci de me le signaler → helias5605", ephemeral=False)


@client.tree.command(name='events', description='Afficher les événement en cours')
async def events(interaction: discord.Interaction):
    try:
        evenements = await display_db()
        now = datetime.now()
        embed = discord.Embed(title="Liste des événements ouverts", color=discord.Color.blue())
        for evenement in evenements:
            if evenement is not None:
                embed.add_field(
                    name=f"Événement {evenement[1]}",
                    value=f"Date: {evenement[2]}\nAuteur: {evenement[3]}\nID: {evenement[0]}",
                    inline=False
                )
        embed.set_footer(text=f"Demandé par {interaction.user} - Date & heure : {now.strftime('%d/%m/%Y %H:%M')}")
        embed.set_author(name=f"AtlantaVR - {interaction.user}", icon_url=f"{client.user.avatar}")
        # embed.set_image(url="https://cdn.discordapp.com/attachments/1118913269776793670/1199095326787764355/"
        #                     "banniere_discord.png?ex=65ca860c&is=65b8110c&hm=352d1d2e87ccb52ca02a4fda942c0fb5"
        #                     "549bdcff1c6fa2a71472363f141a3717&")
        await interaction.response.send_message(embed=embed, ephemeral=False)
    except Exception as e:
        await interaction.response.send_message(f"Une erreur inattendue est survenue : {e}\n"
                                                "Merci de me le signaler → helias5605", ephemeral=False)


@client.tree.command(name='clear', description="Purger un certain nombre de messages")
@app_commands.describe(montant="Le nombre de messages a supprimer")
@commands.has_permissions(manage_messages=True)
async def clear(interaction, montant: int):
    if 0 < montant <= 100:
        await interaction.response.defer()
        await interaction.followup.send(content="Nettoyage terminé")
    else:
        await interaction.response.send_message("Nombre de messages à supprimer trop élevé :(", ephemeral=False)


@client.tree.command(name='reserver', description="Permet de réserver un rôle pour un événement")
@app_commands.describe(id_evenement="Le nombre de messages a supprimer")
@app_commands.describe(rôle="Le nombre de messages a supprimer")
async def select(interaction: discord.Interaction, id_evenement: int, rôle: str):
    try:
        nb = 0
        stock = None
        evenement = await display_db()
        while nb < len(evenement):
            if evenement[nb][0] == id_evenement:
                break
            nb += 1
        if nb != 0:
            for i in range(len(evenement[nb][4].split(", "))):
                if evenement[nb][4].split(', ')[i] == rôle:
                    embed = discord.Embed(title=f"Événement {evenement[nb][1]} du {evenement[nb][2]}",
                                          color=discord.Color.blue())
                    embed.add_field(
                        name=f"Rôle {i + 1} - {evenement[nb][4].split(', ')[i]}",
                        value=stock,
                        inline=False
                    )
                    embed.set_footer(text=f"Créé par {evenement[nb][3]} - ID : {evenement[nb][0]}")
                    embed.set_image(url="https://cdn.discordapp.com/attachments/1118913269776793670/1199095326787764355/"
                                        "banniere_discord.png?ex=65ca860c&is=65b8110c&hm=352d1d2e87ccb52ca02a4fda942c0fb5"
                                        "549bdcff1c6fa2a71472363f141a3717&")
                    await interaction.response.send_message(embed=embed, ephemeral=False)
                    break
        else:
            await interaction.response.send_message("ID non trouvé dans les events actifs", ephemeral=False)
    except Exception as e:
        await interaction.response.send_message(f"Une erreur inattendue est survenue : {e}\n"
                                                "Merci de me le signaler → helias5605", ephemeral=False)



@client.tree.command(name='ping', description="Ping notre bot !")
async def ping(interaction: discord.Interaction):
    latency = round(client.latency * 1000)
    await interaction.response.send_message(f"Pong {interaction.user.mention} ! Latence: {latency}ms", ephemeral=False)


@client.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        message = await ctx.send(f"Cette commande n'existe pas. Veuillez saisir une commande valide.")
    else:
        message = await ctx.send(f"Une erreur est survenue : {error}")
    await asyncio.sleep(4)
    await message.delete()


@client.event
async def on_ready():
    total_members = sum(guild.member_count for guild in client.guilds)
    activity = discord.Activity(type=discord.ActivityType.watching, name=f"{total_members} membres")
    await client.change_presence(activity=activity)
    try:
        synced = await client.tree.sync()
        print(f'SUCCESS → Synced {len(synced)} commands(s)')
    except Exception as e:
        print(e)
    print(f' → Logged on as {client.user}!')


client.run(data['token'])
