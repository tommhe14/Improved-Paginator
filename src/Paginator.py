from __future__ import annotations

import discord
from discord.ext import commands

button_data = {}

class Simple(discord.ui.View):
    """
    Embed Paginator.

    Parameters:
    ----------
    timeout: int
        How long the Paginator should timeout in, after the last interaction. (In seconds) (Overrides default of 60)
    PreviousButton: discord.ui.Button
        Overrides default previous button.
    NextButton: discord.ui.Button
        Overrides default next button.
    PageCounterStyle: discord.ButtonStyle
        Overrides default page counter style.
    InitialPage: int
        Page to start the pagination on.
    AllowExtInput: bool
        Overrides ability for 3rd party to interract with button.
    """

    def __init__(self, *,
                 timeout: int = 60,
                 PreviousButton: discord.ui.Button = discord.ui.Button(emoji=discord.PartialEmoji(name="\U000025c0")),
                 NextButton: discord.ui.Button = discord.ui.Button(emoji=discord.PartialEmoji(name="\U000025b6")),
                 PageCounterStyle: discord.ButtonStyle = discord.ButtonStyle.grey,
                 InitialPage: int = 0, AllowExtInput: bool = False,
                 ephemeral: bool = False) -> None:
        self.PreviousButton = PreviousButton
        self.NextButton = NextButton
        self.PageCounterStyle = PageCounterStyle
        self.InitialPage = InitialPage
        self.AllowExtInput = AllowExtInput
        self.ephemeral = ephemeral
        
        self.pages = None
        self.ctx = None
        self.message = None
        self.current_page = None
        self.page_counter = None
        self.total_page_count = None

        super().__init__(timeout=timeout)

    async def start(self, ctx: discord.Interaction|commands.Context, pages: list[discord.Embed]):

        if isinstance(ctx, discord.Interaction):
            ctx = await commands.Context.from_interaction(ctx)

        self.pages = pages
        self.total_page_count = len(pages)
        self.ctx = ctx
        self.current_page = self.InitialPage

        self.PreviousButton.callback = self.previous_button_callback
        self.NextButton.callback = self.next_button_callback

        self.page_counter = SimplePaginatorPageCounter(style=self.PageCounterStyle,
                                                    TotalPages=self.total_page_count,
                                                    InitialPage=self.InitialPage,
                                                    pages=self.pages)

        self.add_item(self.PreviousButton)
        self.add_item(self.page_counter)
        self.add_item(self.NextButton)

        message = await ctx.send(embed=self.pages[self.InitialPage], view=self, ephemeral=self.ephemeral)

        self.InitialPage = self.InitialPage if self.InitialPage is not None else 0

        button_data.update(
                {
                message.id:
                    {
                        "self":self,
                        "message":message,
                        "page_counter":self.page_counter,
                        "current_page":self.InitialPage,
                        "total_page_count":self.total_page_count
                    }
                }
                        )



    async def previous(self, interaction):

        self.current_page = button_data[interaction.message.id]["current_page"]
        self.total_page_count = button_data[interaction.message.id]["total_page_count"]
        self.message = button_data[interaction.message.id]["message"]
        self.pages = button_data[interaction.message.id]["page_counter"].pages
        self.current_page = button_data[interaction.message.id]["current_page"]
        self.page_counter = button_data[interaction.message.id]["page_counter"]
        
        if self.current_page == 0:
            self.current_page = self.total_page_count - 1
        else:
            self.current_page -= 1

        self.page_counter.label = f"{self.current_page + 1}/{self.total_page_count}"

        button_data[interaction.message.id]["self"].page_counter.current_page = self.current_page
        button_data[interaction.message.id]["self"].page_counter.total_pages = self.total_page_count
        button_data[interaction.message.id]["page_counter"] = self.page_counter
        button_data[interaction.message.id]["current_page"] = self.current_page

        await self.message.edit(embed=self.pages[self.current_page], view=button_data[interaction.message.id]["self"])


    async def next(self, interaction):

        self.current_page = button_data[interaction.message.id]["current_page"]
        self.total_page_count = button_data[interaction.message.id]["total_page_count"]
        self.message = button_data[interaction.message.id]["message"]
        self.pages = button_data[interaction.message.id]["page_counter"].pages
        self.page_counter = button_data[interaction.message.id]["page_counter"]

        if self.current_page == self.total_page_count - 1:
            self.current_page = 0
        else:
            self.current_page += 1

        self.page_counter.label = f"{self.current_page + 1}/{self.total_page_count}"

        button_data[interaction.message.id]["self"].page_counter.current_page = self.current_page
        button_data[interaction.message.id]["self"].page_counter.total_pages = self.total_page_count
        button_data[interaction.message.id]["page_counter"] = self.page_counter
        button_data[interaction.message.id]["current_page"] = self.current_page

        await self.message.edit(embed=self.pages[self.current_page], view=button_data[interaction.message.id]["self"])
        

    async def next_button_callback(self, interaction: discord.Interaction):
        self.ctx.author = button_data[interaction.message.id]["self"].ctx.author
        if interaction.user != self.ctx.author and self.AllowExtInput:
            embed = discord.Embed(description="You cannot control this pagination because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.next(interaction)
        await interaction.response.defer()

    async def previous_button_callback(self, interaction: discord.Interaction):
        self.ctx.author = button_data[interaction.message.id]["self"].ctx.author
        if interaction.user != self.ctx.author and self.AllowExtInput:
            embed = discord.Embed(description="You cannot control this pagination because you did not execute it.",
                                  color=discord.Colour.red())
            return await interaction.response.send_message(embed=embed, ephemeral=True)
        await self.previous(interaction)
        await interaction.response.defer()



class SimplePaginatorPageCounter(discord.ui.Button):
    def __init__(self, style: discord.ButtonStyle, TotalPages, InitialPage, pages):
        self.current_page = InitialPage
        self.total_pages = TotalPages
        super().__init__(label=f"{InitialPage + 1}/{TotalPages}", style=style, disabled=True)
        self.pages = pages
    
        
