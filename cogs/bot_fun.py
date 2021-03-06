# System import
import asyncio
import io
from random import random
import logging

# Third party import
from datetime import datetime
import discord
from decimal import Decimal, InvalidOperation
from discord.ext import commands

# personal files
import tools


class fun:
    def __init__(self, bot):
        self.bot = bot

    #  async def on_ready(self):
    #    self.bot.loop.create_task(self.status_task())

    async def on_message(self, message):
        # Only listen to messages from other people and none bots
        if message.author == self.bot.user or message.author.bot:
            return

        # Handle AI code
        if self.bot.user.id in message.raw_mentions:
            if "ask me" in message.content:
                return await self.ask_math(message)
            talk_msg = message.content.split(' ')
            # make sure we get there are text passed the mention
            if len(talk_msg) > 1:
                # activate bot's AI from Dialogflow
                query = ' '.join([word for word in talk_msg if not word.startswith('<')])
                msg = await self.bot.send_message(message.channel, "{}".format(tools.loading_emoji))
                logging.debug("sending: {}".format(query))
                logging.info("User {} talking to bot in {}:{}".format(
                    message.author.name, message.channel.server.name, message.channel.name))
                aireply = tools.talk_ai(query, message.channel.id).replace('@@username', message.author.name)
                logging.debug(aireply)
                return await self.bot.edit_message(msg, new_content=aireply)

        '''
        # on random make him use ai for texts
        if random() < 0.01 and not (message.content.startswith(self.bot.user.mention)
                                    or message.content.startswith(tools.prefix)):
            query = message.content
            msg = await self.bot.send_message(message.channel, "{}".format(tools.loading_emoji))
            logging.debug("sending: {}".format(query))
            logging.info("User {} talking to bot in {}:{}".format(
                message.author.name, message.channel.server.name, message.channel.name))
            aireply = tools.talk_ai(query, message.channel.id).replace('@@username', message.author.name)
            logging.debug(aireply)
            return await self.bot.edit_message(msg, new_content=aireply)
        '''

        # Do not echo if a mention in beginning or prefix
        if random() < 0.01 and not (message.content.startswith(self.bot.user.mention)
                                    or message.content.startswith(tools.prefix)):
            await self.bot.add_reaction(message, emoji=tools.evil_emoji)
            await asyncio.sleep(1.5)
            # if message was a png/jpeg, add pickle image to the image and upload
            image = tools.paste_image_from_source(message.content, self.bot.user.avatar_url)
            if image:
                try:
                    with io.BytesIO(image) as new_image:
                        filename = "{0}-{1}.{2}".format("hehe", datetime.now().strftime("%d-%m-%y_%H%M"), "png")
                        return await self.bot.send_file(message.channel, fp=new_image, filename=filename)
                except Exception:
                    logging.exception("Exception when generating an image")
                    pass
            else:
                bot_message = "{0}!!".format(message.content.capitalize())
                embed = discord.Embed(color=message.author.color)
                embed.add_field(name="Hehe...", value=bot_message, inline=False)
                embed.set_thumbnail(url=self.bot.user.avatar_url)
                return await self.bot.send_message(message.channel, embed=embed)

    async def on_command_error(self, error, ctx):
        logging.error(error)
        channel = ctx.message.channel
        if isinstance(error, commands.CommandOnCooldown):
            command = ctx.invoked_subcommand
            return await self.bot.send_message(
                channel, ("Whoa there, {0}, you've been using {1} too fast. "
                          + "Try again after a bit.").format(
                    ctx.message.author.mention, command
                ))

    async def status_task(self):
        channel = self.bot.get_channel(tools.channel_spam_id)
        while self.bot.is_logged_in:
            if random() < 0.25 and channel is not None:
                ctx = await self.bot.send_message(channel, "New mood")
                await asyncio.sleep(2.0)
                await self.get_mood(ctx)
            await asyncio.sleep(360.0)

    # [mood] command. Generates random mood whenever it is called.
    @commands.command(pass_context=True)
    async def mood(self, ctx):
        """Generate text with a custom emoji from server"""
        await self.get_mood(ctx.message)

    async def get_mood(self, message):
        # Retrieve a random item from custom emojis from the server
        # Make sure the emojis are unrestricted otherwise they will be ignored
        custom_emojis = [emoji for emoji in self.bot.get_all_emojis() if not emoji.roles]

        if not custom_emojis:
            return await self.bot.say((
                "Aww... "
                "There's no custom emojis I can express in this server. "
                "In that case my mood is :poop:"))

        # Retrieve random emoji retrieved from server and format it to be shown on chat.
        emoji_string = tools.format_emoji(
            tools.get_random_item(custom_emojis))

        # Display on Discord
        new_msg = await self.bot.send_message(message.channel, "I'm feeling... " + emoji_string)
        await asyncio.sleep(1)
        await self.bot.edit_message(new_msg, new_content=(
                new_msg.content + "\n\t...for now anyways."))

    # [choose] command.
    @commands.command()
    async def choose(self, *args):
        """Choose one or more items asked"""
        items = [text.replace(',', '') for text in args if text.lower() != "or"]
        size = len(items)
        if size == 0:
            return await self.bot.say("There wasn't anything to choose from. :cry:")
        elif size == 1:
            return await self.bot.say(
                "Well... I guess {0} since that's the only option!".format(
                    str(items[0])))
        else:
            item_chosen = tools.get_random_item(items)
            if item_chosen == "me":
                item_chosen = "you"
            return await self.bot.say("I choose... {0}!".format(
                str(item_chosen)))

    # [goodbye] command. Logs the bot off discord if owner calls it;
    # otherwise, bot will simply say goodbye to the caller.
    # uses 'dad' variable in config.py
    @commands.command(pass_context=True)
    async def goodbye(self, ctx):
        """Sends a goodbye text; stops if host"""
        if ctx.message.author.id != tools.owner_id:
            await self.bot.add_reaction(ctx.message, emoji=tools.cross_mark_emoji)
            return await self.bot.say("Oh! Goodbye, "
                                      + ctx.message.author.mention
                                      + "! See you again soon.")
        await self.bot.add_reaction(ctx.message, emoji=tools.check_mark_emoji)
        await self.bot.say("I'm logging off. Goodbye frineds!")
        await self.bot.close()

    # [poke] command. If entered a user who is not the sender nor the bot,
    # it will mention that the sender poked the user.
    # Otherwise, it will assume the sender is poking the bot.
    @commands.command(pass_context=True, aliases=['interact', 'hug', 'pet', 'pat'])
    async def poke(self, ctx, member: discord.Member = None):
        """ poke someone. Assumes itself if no mention.

            Can also use -interact, -hug, or -pet instead
        """
        action_dict = {
            'poke': "poking",
            'hug': "hugging",
            'pet': "petting",
            'pat': "patting",
            'interact': "interacting with"
        }
        source = ctx.message.author
        poking_bot = False if (member is not None and member != self.bot.user) else True
        poker_bot = True if (member is not None and member == source) else False
        if not poking_bot and poker_bot:
            await self.bot.say('I\'m {1} you, {0}!'
                               .format(source.mention,
                                       action_dict[ctx.invoked_with]))
        elif poking_bot:
            await self.bot.say('Hello, {0}! You are {1} me!'
                               .format(source.mention,
                                       action_dict[ctx.invoked_with]))
        else:
            await self.bot.say('Hey {0}, {1} is {2} you!'
                               .format(member.mention,
                                       source.mention,
                                       action_dict[ctx.invoked_with]))

    @commands.group(pass_context=True)
    @commands.cooldown(rate=10, per=60, type=commands.BucketType.user)
    async def ask(self, ctx):
        if ctx.invoked_subcommand is None:
            return await self.bot.say("What kind of question do you want to be asked? Try the help for options.")

    @ask.command(pass_context=True)
    @commands.cooldown(rate=10, per=60, type=commands.BucketType.user)
    async def me(self, ctx):
        """Asks you a math question.

        Careful, you are timed!
        """
        await self.ask_math(ctx.message)

    @ask.group(pass_context=True)
    @commands.cooldown(rate=10, per=60, type=commands.BucketType.user)
    async def trivia(self, ctx):
        """Ask you for a random trivia question."""
        if ctx.subcommand_passed != "anime":
            return await self.ask_trivia(ctx.message)

    @trivia.command(pass_context=True)
    @commands.cooldown(rate=10, per=60, type=commands.BucketType.user)
    async def anime(self, ctx):
        """Ask you for a random anime trivia question."""
        return await self.ask_trivia(ctx.message, 31)

    async def ask_trivia(self, message, category: int=None):
        question_dict = tools.get_trivia_question(category=category)
        if not question_dict.get('error', ""):
            difficulty_name = question_dict['difficulty']
            difficulty = "Difficulty: {0}".format(difficulty_name.title())
            question = question_dict['question']
            choices = '\n\t'.join(
                ("({0}) {1}".format(number, choice)
                 for number, choice
                 in enumerate(question_dict['choices'], 1)))
            time = 30.0
            footer = ":: Answer by entering the number. You have {0} seconds. ::".format(time)

            message_block = "I have a question for you: ```{0}\n\n{1}\n\t{2}\n\n{3}```".format(
                difficulty, question, choices, footer)
            await self.bot.send_message(message.channel, message_block)
            try:
                reply_message = await self.bot.wait_for_message(
                    author=message.author,
                    channel=message.channel,
                    timeout=time)
            except asyncio.TimeoutError:
                reply_message = None
                pass
            if reply_message is None:
                return await self.bot.send_message(message.channel,
                                                   "Oh, sorry, you took too long. Try again")

            correct_num = question_dict['correct']
            answer_num = None
            if reply_message.content:
                try:
                    answer_num = int(reply_message.content.split(' ')[0])
                except ValueError:
                    pass

            if answer_num and answer_num == correct_num:
                if difficulty_name == "medium":
                    coin_amount = 2
                elif difficulty_name == "hard":
                    coin_amount = 3
                else:
                    coin_amount = 1
                await self.bot.add_reaction(reply_message, emoji=tools.check_mark_emoji)
                await self.bot.send_message(message.channel, "That's correct!")
                kyoncoin = tools.KyonCoin()
                coins = kyoncoin.update_coins(message.server.id, message.author.id, coin_amount)
                await self.bot.send_message(message.channel, "You have {0} KyonCoins now!".format(coins))
            else:
                await self.bot.add_reaction(reply_message, emoji=tools.cross_mark_emoji)
                return await self.bot.send_message(message.channel,
                                                   "Sorry but the corrrect answer is: {0}".format(
                                                       question_dict['correct_answer']))
        else:
            return await self.bot.send_message(message.channel, question_dict['error'])

    @commands.command(pass_context=True)
    async def meme(self, ctx, *, args: str=None):
        """Meme Generator. Format is <top>;<bottom>|<img_url>

        Alternatively, image could be an attachment so format is <top>;<bottom>"""

        loading_msg = await self.bot.send_message(ctx.message.channel,
                                                  "Making memes, bear with me for a bit...")
        message = args
        img_url = None
        gif_index = None
        if args:
            msg_list = args.split('|', maxsplit=2)
            message = msg_list[0]
            if len(msg_list) > 1:
                img_url = msg_list[1].strip()
            if len(msg_list) > 2:
                try:
                    gif_index = int(msg_list[2])
                    logging.debug("gif_index = {}".format(gif_index))
                except ValueError:
                    logging.warning("Not a number")

        # Check if an attachment is present. Prioritize that
        if ctx.message.attachments and ctx.message.attachments[0].get('url'):
            img_url = ctx.message.attachments[0].get('url')
        if not img_url:
            # If no image provided, use a random subreddit
            subreddit = tools.get_random_item(list(tools.subreddits.values()))
            img_dict = tools.get_subreddit_image_list(subreddit)
            if not img_dict.get('error'):
                img_item = tools.get_random_item(img_dict.get('img_list', []))
                img_url = img_item if img_item else None

        img_result = tools.generate_meme_from_text(message, img_url, gif_index)
        if img_result:
            try:
                with io.BytesIO(img_result) as new_image:
                    filename = "{0}-{1}.{2}".format("meme", datetime.now().strftime("%d-%m-%y_%H%M"), "png")
                    await self.bot.delete_message(loading_msg)
                    return await self.bot.send_file(ctx.message.channel, fp=new_image, filename=filename)
            except discord.HTTPException:
                logging.exception("Exception when uploading meme image.")
                return await self.bot.edit_message(loading_msg,
                                                   new_content="The image I got was way too big I'm sorry :sob:")
            except Exception:
                logging.exception("Exception when trying to generate meme image")
                pass
        return await self.bot.edit_message(loading_msg, "wut")

    # i'm not convinced this works
    @commands.command(pass_context=True, aliases=['cat', 'pirate'])
    async def joke_accent(self, ctx, *, args: str=None):
        """Joke accent translator. Format is -[mode] [phrase]. Currently supported modes are cat and pirate."""
        mode = ctx.invoked_with
        string = args
        bot_message = "{0}: {1}".format(ctx.message.author.mention , tools.Converter(string, mode)) #this makes it so that it almost mirrors the "copy cat" random func
        embed = discord.Embed(color=ctx.message.author.color)
        title = "Placeholder. You shouldn't see this."
        if mode == "cat":
            title = "Nyaa~"
        elif mode == 'pirate':
            title = "Shiver me timbers!"
        embed.add_field(name=title, value=bot_message, inline=False)
        embed.set_thumbnail(url=ctx.message.author.avatar_url)
        await self.bot.delete_message(ctx.message)
        return await self.bot.send_message(ctx.message.channel, embed=embed)

    @commands.group(pass_context=True)
    async def kyon(self, ctx):
        """Shows how many coins you have."""
        if ctx.invoked_subcommand is None:
            kyoncoin = tools.KyonCoin()
            coins = kyoncoin.get_coins(ctx.message.server.id, ctx.message.author.id)
            return await self.bot.say("{0}, you have {1} KyonCoins".format(ctx.message.author.mention, coins))

    async def ask_math(self, message):
        question, num_answer = tools.get_random_math_question()
        await self.bot.send_message(
            message.channel,
            "Ok, {0}, what is {1}?".format(
                message.author.mention,
                question))
        try:
            reply_message = await self.bot.wait_for_message(
                author=message.author,
                channel=message.channel,
                timeout=20.0)
        except asyncio.TimeoutError:
            reply_message = None
            pass
        if reply_message is None:
            return await self.bot.send_message(message.channel, "Oh, sorry, you took too long. Try again")
        message_text = reply_message.content
        reply = message_text
        num_input = None
        if message_text:
            try:
                reply = message_text.split(' ')[0]  # only look at first word
                num_input = Decimal(reply)
            except InvalidOperation:
                pass
        answer_correct = num_input is not None and num_answer == num_input
        bot_reply = "You replied with: {0}\n{1}".format(
            num_input if (num_input is not None)  # If input was a number, show
            else reply,  # Otherwise, display what was entered
            "That's right! Thanks for playing!"  # Result if right
            if answer_correct
            else ("Oh no that wasn't right..."
                  "The answer is {0}!").format(num_answer)  # Result if wrong
        )
        await self.bot.send_message(message.channel, bot_reply)
        if answer_correct:
            await self.bot.add_reaction(reply_message, emoji=tools.check_mark_emoji)
            kyoncoin = tools.KyonCoin()
            coins = kyoncoin.update_coins(message.server.id, message.author.id, 1)
            await self.bot.send_message(message.channel, "You have {0} KyonCoins now!".format(coins))
        else:
            await self.bot.add_reaction(reply_message, emoji=tools.cross_mark_emoji)


def setup(bot):
    bot.add_cog(fun(bot))
