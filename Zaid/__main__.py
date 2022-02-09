import html
import os
import json
import importlib
import time
import re
import sys
import traceback
import Zaid.modules.sql.users_sql as sql
from sys import argv
from typing import Optional
from telegram import __version__ as peler
from platform import python_version as memek
from Zaid import (
    ALLOW_EXCL,
    CERT_PATH,
    DONATION_LINK,
    LOGGER,
    OWNER_ID,
    PORT,
    SUPPORT_CHAT,
    TOKEN,
    URL,
    WEBHOOK,
    SUPPORT_CHAT,
    dispatcher,
    StartTime,
    telethn,
    pbot,
    updater,
)

# needed to dynamically load modules
# NOTE: Module order is not guaranteed, specify that in the config file!
from Zaid.modules import ALL_MODULES
from Zaid.modules.helper_funcs.chat_status import is_user_admin
from Zaid.modules.helper_funcs.misc import paginate_modules
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.error import (
    BadRequest,
    ChatMigrated,
    NetworkError,
    TelegramError,
    TimedOut,
    Unauthorized,
)
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from telegram.ext.dispatcher import DispatcherHandlerStop, run_async
from telegram.utils.helpers import escape_markdown


def get_readable_time(seconds: int) -> str:
    count = 0
    ping_time = ""
    time_list = []
    time_suffix_list = ["s", "m", "h", "days"]

    while count < 4:
        count += 1
        remainder, result = divmod(seconds, 60) if count < 3 else divmod(seconds, 24)
        if seconds == 0 and remainder == 0:
            break
        time_list.append(int(result))
        seconds = int(remainder)

    for x in range(len(time_list)):
        time_list[x] = str(time_list[x]) + time_suffix_list[x]
    if len(time_list) == 4:
        ping_time += time_list.pop() + ", "

    time_list.reverse()
    ping_time += ":".join(time_list)

    return ping_time


LOVELY_MENU = """
Hi {}
I'm Lovely group management/Music bot.

I can do a variety of things, most common of em are:
- Restrict users with ban permissions.
- Greet users with media + text and buttons, with proper formatting.
- Restrict users who flood your chat using my anti-flood module.
- Warn users according to the options set and restrict em accordingly.
- Save notes and filters with proper formatting and reply markup.
- I can also Play Music in groups

Theres even more! this is just the tip of the iceberg. Do note I need
to be promoted with proper admin permissions to function properly. 
Else I won't be able to function as said.

Click on help to learn more and Join @Lovelyappeal for report bugs!
"""

Lovelybuttons = [
     [
        InlineKeyboardButton(text="Add Lovely", url="https://t.me/LOVELYR_OBOT?startgroup=true"),
        InlineKeyboardButton(text="Tutorial", callback_data="lovelyx_"),
        InlineKeyboardButton(text="Donate", url="t.me/TUSHAR204"),         
     ],
     [  
        InlineKeyboardButton(text="Support", url="https://t.me/LOVELYAPPEAL"),
        InlineKeyboardButton(text="Help", callback_data="emiko_"),
        InlineKeyboardButton(text="Update", url="https://t.me/ABOUTVEDMAT"),
     ], 
     [
       InlineKeyboardButton(text="Music Bot", callback_data="shikhar_"),
     ],
]


LOVELYX_VIDAA = """https://telegra.ph/file/34f30bd06c6f62778f075.mp4"""


LOVELY_HELP = """
༆*Lovely comes with many special features in it*༆
꧁*check all button below to explore every commands of lovely*꧂
𖣘 *All commands can either be used with* `/` *or* `!`.
𖣘 *If you facing any issue or find any bugs in any command then you can report it in @LOVELYAPPEAL* .
"""

LOVELY_BASIC = """This are some *Basic commands* which will help you to manage group easily by Lovely"""

DONATE_STRING = """Heya, glad to hear you want to donate!
 You can support the project by contacting @TUSHAR204 \
 Supporting isnt always financial! \
 Those who cannot provide monetary support are welcome to help us develop the bot at ."""

IMPORTED = {}
MIGRATEABLE = []
HELPABLE = {}
STATS = []
USER_INFO = []
DATA_IMPORT = []
DATA_EXPORT = []
CHAT_SETTINGS = {}
USER_SETTINGS = {}

for module_name in ALL_MODULES:
    imported_module = importlib.import_module("Zaid.modules." + module_name)
    if not hasattr(imported_module, "__mod_name__"):
        imported_module.__mod_name__ = imported_module.__name__

    if imported_module.__mod_name__.lower() not in IMPORTED:
        IMPORTED[imported_module.__mod_name__.lower()] = imported_module
    else:
        raise Exception("Can't have two modules with the same name! Please change one")

    if hasattr(imported_module, "__help__") and imported_module.__help__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module

    # Chats to migrate on chat_migrated events
    if hasattr(imported_module, "__migrate__"):
        MIGRATEABLE.append(imported_module)

    if hasattr(imported_module, "__stats__"):
        STATS.append(imported_module)

    if hasattr(imported_module, "__user_info__"):
        USER_INFO.append(imported_module)

    if hasattr(imported_module, "__import_data__"):
        DATA_IMPORT.append(imported_module)

    if hasattr(imported_module, "__export_data__"):
        DATA_EXPORT.append(imported_module)

    if hasattr(imported_module, "__chat_settings__"):
        CHAT_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__user_settings__"):
        USER_SETTINGS[imported_module.__mod_name__.lower()] = imported_module

    if hasattr(imported_module, "__lovely_basic__") and imported_module.__lovely_basic__:
        HELPABLE[imported_module.__mod_name__.lower()] = imported_module


# do not async
def send_help(chat_id, text, keyboard=None):
    if not keyboard:
        keyboard = InlineKeyboardMarkup(paginate_modules(0, HELPABLE, "help"))
    dispatcher.bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode=ParseMode.MARKDOWN,
        disable_web_page_preview=True,
        reply_markup=keyboard,
    )


def test(update: Update, context: CallbackContext):
    # pprint(eval(str(update)))
    # update.effective_message.reply_text("Hola tester! _I_ *have* `markdown`", parse_mode=ParseMode.MARKDOWN)
    update.effective_message.reply_text("This person edited a message")
    print(update.effective_message)


def start(update: Update, context: CallbackContext):
    args = context.args
    uptime = get_readable_time((time.time() - StartTime))
    if update.effective_chat.type == "private":
        if len(args) >= 1:
            if args[0].lower() == "help":
                send_help(update.effective_chat.id, HELP_STRINGS)
            elif args[0].lower().startswith("ghelp_"):
                mod = args[0].lower().split("_", 1)[1]
                if not HELPABLE.get(mod, False):
                    return
                send_help(
                    update.effective_chat.id,
                    HELPABLE[mod].__help__,
                    InlineKeyboardMarkup(
                        [[InlineKeyboardButton(text="Go Back", callback_data="help_back")]]
                    ),
                )

            elif args[0].lower().startswith("stngs_"):
                match = re.match("stngs_(.*)", args[0].lower())
                chat = dispatcher.bot.getChat(match.group(1))

                if is_user_admin(chat, update.effective_user.id):
                    send_settings(match.group(1), update.effective_user.id, False)
                else:
                    send_settings(match.group(1), update.effective_user.id, True)

            elif args[0][1:].isdigit() and "rules" in IMPORTED:
                IMPORTED["rules"].send_rules(update, args[0], from_pm=True)

        else:
            first_name = update.effective_user.first_name
            update.effective_message.reply_text(
                LOVELY_MENU.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),                        
                reply_markup=InlineKeyboardMarkup(Lovelybuttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
            )
    else:
        update.effective_message.reply_text(
            "*Lovely is alive* use below buttons to explore my features in group or pm!",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Open in private chat",
                            url="t.me/{}?start".format(context.bot.username),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Explore here", callback_data="emiko_back"
                        ),
                    ],
                ]
            ),
        )

def error_handler(update, context):
    """Log the error and send a telegram message to notify the developer."""
    # Log the error before we do anything else, so we can see it even if something breaks.
    LOGGER.error(msg="Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns the usual python message about an exception, but as a
    # list of strings rather than a single string, so we have to join them together.
    tb_list = traceback.format_exception(
        None, context.error, context.error.__traceback__
    )
    tb = "".join(tb_list)

    # Build the message with some markup and additional information about what happened.
    message = (
        "An exception was raised while handling an update\n"
        "<pre>update = {}</pre>\n\n"
        "<pre>{}</pre>"
    ).format(
        html.escape(json.dumps(update.to_dict(), indent=2, ensure_ascii=False)),
        html.escape(tb),
    )

    if len(message) >= 4096:
        message = message[:4096]
    # Finally, send the message
    context.bot.send_message(chat_id=OWNER_ID, text=message, parse_mode=ParseMode.HTML)


# for test purposes
def error_callback(update: Update, context: CallbackContext):
    error = context.error
    try:
        raise error
    except Unauthorized:
        print("no nono1")
        print(error)
        # remove update.message.chat_id from conversation list
    except BadRequest:
        print("no nono2")
        print("BadRequest caught")
        print(error)

        # handle malformed requests - read more below!
    except TimedOut:
        print("no nono3")
        # handle slow connection problems
    except NetworkError:
        print("no nono4")
        # handle other connection problems
    except ChatMigrated as err:
        print("no nono5")
        print(err)
        # the chat_id of a group has changed, use e.new_chat_id instead
    except TelegramError:
        print(error)
        # handle all other telegram related errors


def help_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"help_module\((.+?)\)", query.data)
    prev_match = re.match(r"help_prev\((.+?)\)", query.data)
    next_match = re.match(r"help_next\((.+?)\)", query.data)
    back_match = re.match(r"help_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__help__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                  [
                    [InlineKeyboardButton(text="Updates", url="t.me/ABOUTVEDMAT"), InlineKeyboardButton(text="Support", url="t.me/LOVELYAPPEAL")],
                    [InlineKeyboardButton(text="Go back", callback_data="help_back"), InlineKeyboardButton(text="Add Lovely", url="t.me/LOVELYR_OBOT?startgroup=true")]
                  ]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=LOVELY_HELP,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=LOVELY_HELP,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=LOVELY_HELP,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "help")
                ),
            )

        # ensure no spinny white circle
        context.bot.answer_callback_query(query.id)
        # query.message.delete()

    except BadRequest:
        pass

def lovelybasic_button(update, context):
    query = update.callback_query
    mod_match = re.match(r"lovelybasic_module\((.+?)\)", query.data)
    prev_match = re.match(r"lovelybasic_prev\((.+?)\)", query.data)
    next_match = re.match(r"lovelybasic_next\((.+?)\)", query.data)
    back_match = re.match(r"lovelybasic_back", query.data)

    print(query.message.chat.id)

    try:
        if mod_match:
            module = mod_match.group(1)
            text = (
                "Here is the help for the *{}* module:\n".format(
                    HELPABLE[module].__mod_name__
                )
                + HELPABLE[module].__lovely_basic__
            )
            query.message.edit_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
                reply_markup=InlineKeyboardMarkup(
                  [
                    [InlineKeyboardButton(text="Updates", url="t.me/ABOUTVEDMAT"), InlineKeyboardButton(text="Support", url="t.me/LOVELYAPPEAL")],
                    [InlineKeyboardButton(text="Go back", callback_data="lovelybasic_back"), InlineKeyboardButton(text="Add Lovely", url="t.me/LOVELYR_OBOT?startgroup=true")]
                  ]
                ),
            )

        elif prev_match:
            curr_page = int(prev_match.group(1))
            query.message.edit_text(
                text=LOVELY_BASIC,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "lovelybasic")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=LOVELY_BASIC,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "lovelybasic")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=LOVELY_BASIC,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, HELPABLE, "lovelybasic")
                ),
            )

    except BadRequest:
        pass

def emiko_about_callback(update, context):
    query = update.callback_query
    if query.data == "emiko_":
        query.message.edit_text(
       text="""Hey there! My name is *Lovely 🇮🇳*
I'm a Queen For Fun and help admins manage their groups! 
Have a look at the following for an idea of some of the things I can help you with.
*Main commands available:*
 • /help: PM's you this message and also you can use this in group
 • /help <module name>: PM's you info about that module.
 • /settings:
   • in PM: will send you your settings for all supported modules.
   • in a group: will redirect you to pm, with all that chat's settings.

All commands can either be used with / or !.
And the following:""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Basic", callback_data="lovelybasic_back"),
                    InlineKeyboardButton(text="All", callback_data="help_back"),
                    InlineKeyboardButton(text="Advanced", callback_data="lovelyx_advance"),
                 ],      
                 [
                    InlineKeyboardButton(text="Fun and extra", callback_data="lovelyx_fe"),
                    InlineKeyboardButton(text="Back", callback_data="emiko_back"),
                    InlineKeyboardButton(text="Inline", switch_inline_query_current_chat=""),
                 ]
               ]
            ),
        )
    elif query.data == "emiko_back":
        first_name = update.effective_user.first_name
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_text(
                LOVELY_MENU.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(Lovelybuttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )


def lovelyx_about_callback(update, context):
    query = update.callback_query
    if query.data == "lovelyx_":
        query.message.edit_text(
            text="Hi I'm Lovely, one of the fastest and most features for your groups"
                 "\n\nYou can also Play Music groups by using me!",
        parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Add me to Group", url="t.me/LOVELYR_OBOT?startgroup=true"),
                 ],
                 [
                    InlineKeyboardButton(text="Video Tutorial", callback_data="lovelyx_vida"),
                 ],
                 [
                    InlineKeyboardButton(text="Back", callback_data="lovelyx_back"),
                    InlineKeyboardButton(text="Next", callback_data="lovelyx_pro"),
                 ]
                ]
            ),
        )
    elif query.data == "lovelyx_back":
        first_name = update.effective_user.first_name
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_text(
                LOVELY_MENU.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(Lovelybuttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )
    elif query.data == "lovelyx_pro":
        query.message.edit_text(
            text="""<b>Hey, Welcome to Lovely configuration Tutorial
Before we go, I need admin permissions in this chat to work properly
1) Click Manage Group
2) Go to Administrators and add</b> @LOVELYR_OBOT <b>as Admin
3) Giving full permissions make Lovely fully useful</b>""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
              [[InlineKeyboardButton(text="previous", callback_data="lovelyx_"),
                InlineKeyboardButton(text="next", callback_data="lovelyx_help")],               
              ]
            ),
        )

    elif query.data == "lovelyx_help":
        query.message.edit_text(
            text="""*Let's make your group bit effective now
Congragulations, Lovely now ready to manage your group
Here are some essentialt to try on
✗ Admin tools
Basic Admin tools help you to protect and powerup your group
You can ban members, Kick members, Promote someone as admin through commands of bot
✗ Welcomes
Lets set a welcome message to welcome new users coming to your group
send* /setwelcome *[message] to set a welcome message
Also you can Stop entering robots or spammers to your chat by setting welcome captcha 
Refer Help menu to see everything in detail*""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [
                [InlineKeyboardButton(text="previous", callback_data="lovelyx_pro"),
                 InlineKeyboardButton(text="next", callback_data="lovelyx_helpc")]
                ]
            ),
        )

    elif query.data == "lovelyx_helpc":
        query.message.edit_text(
            text="""✗ *Filters*
Filters can be used as automated replies/ban/delete when someone use a word or sentence
For Example if I filter word 'hello' and set reply as 'hi'
Bot will reply as 'hi' when someone say 'hello'
You can add filters by sending /filter [filter name]
✗ *AI Chatbot*
Want someone to chat in group?
Tiana has an intelligent chatbot with multilang support
Let's try it,
Send /chatbot on and reply to any of my messages to see the magic""",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [
                [InlineKeyboardButton(text="previous", callback_data="lovelyx_helpb"),
                 InlineKeyboardButton(text="next", callback_data="lovelyx_helpd")]
                ]
            ),
        )
    elif query.data == "lovelyx_helpd":
        query.message.edit_text(
            text="""✗ *Setting up Notes*
You can save message/media/audio or anything as notes
to get a note simply use # at the beginning of a word
See the image..
You can also set buttons for notes and filters (refer help menu)
✗ *Setting up NightMode*
You can set up NightMode Using /nightmode on/off command.
Note- Night Mode chats get Automatically closed at 12pm(IST)
and Automatically openned at 6am(IST) To Prevent Night Spams.""",
         parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
              [
                [InlineKeyboardButton(text="previous", callback_data="lovelyx_helpc"),
                 InlineKeyboardButton(text="next", callback_data="lovelyx_helpe")]
                ]
            ),
        )
    elif query.data == "lovelyx_term":
        query.message.edit_text(
            text="""✗ *Terms and Conditions:*
- Only your first name, last name (if any) and username (if any) is stored for a convenient communication!
- No group ID or it's messages are stored, we respect everyone's privacy.
- Messages between Bot and you is only infront of your eyes and there is no backuse of it.
- Watch your group, if someone is spamming your group, you can use the report feature of your Telegram Client.
- Do not spam commands, buttons, or anything in bot PM.
*NOTE:* Terms and Conditions might change anytime
*Updates Channel:* @LOVELY\_ROBOTS
*Support Chat:* @PrincexSupport""",
          parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[
                InlineKeyboardButton(text="Back", callback_data="about_")]]
            ),
        )
    elif query.data == "lovelyx_helpe":
        query.message.edit_text(
            text="""So now you are at the end of basic tour. But this is not all I can do.
Send /help in bot pm to access help menu
There are many handy tools to try out. 
And also if you have any suggessions about me, Don't forget to tell them to devs
Again thanks for using me
✗ By using @LOVELYR\_OBOT you are agreed to our terms & conditions""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Help", callback_data="emiko_")],
                [InlineKeyboardButton(text="back", callback_data="lovelyx_helpd"),
                InlineKeyboardButton(text="Main menu", callback_data="lovelyx_")]]
            ),
        )
    elif query.data == "lovelyx_vida":
        query.message.reply_video(
            LOVELYX_VIDAA,
            parse_mode=ParseMode.MARKDOWN,
            ),

    elif query.data == "lovelyx_admin":
        query.message.edit_text(
            text="""Here is the help for the Admins module:

User Commands:
❂ /admins: list of admins in the chat
❂ /pinned: to get the current pinned message.
The Following Commands are Admins only: 
❂ /pin: silently pins the message replied to - add `'loud'` or `'notify'` to give notifs to users
❂ /unpin: unpins the currently pinned message
❂ /invitelink: gets invitelink
❂ /promote: promotes the user replied to
❂ /fullpromote: promotes the user replied to with full rights
❂ /demote: demotes the user replied to
❂ /title <title here>: sets a custom title for an admin that the bot promoted
❂ /admincache: force refresh the admins list
❂ /del: deletes the message you replied to
❂ /purge: deletes all messages between this and the replied to message.
❂ /purge <integer X>: deletes the replied message, and X messages following it if replied to a message.

Rules:
❂ /rules: get the rules for this chat.
❂ /setrules <your rules here>: set the rules for this chat.
❂ /clearrules: clear the rules for this chat.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_basic")]]
            ),
        )

    elif query.data == "lovelyx_bansmute":
        query.message.edit_text(
            text="""Here is the help for the Bans/Mutes module:

*User Commands:*

❂ /kickme: kicks the user who issued the command

*Admins only:*

❂ /ban <userhandle>: bans a user. (via handle, or reply)
❂ /sban <userhandle>: Silently ban a user. Deletes command, Replied message and doesn't reply. (via handle, or reply)
❂ /tban <userhandle> x(m/h/d): bans a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
❂ /unban <userhandle>: unbans a user. (via handle, or reply)
❂ /kick <userhandle>: kicks a user out of the group, (via handle, or reply)
❂ /mute <userhandle>: silences a user. Can also be used as a reply, muting the replied to user.
❂ /tmute <userhandle> x(m/h/d): mutes a user for x time. (via handle, or reply). m = minutes, h = hours, d = days.
❂ /unmute <userhandle>: unmutes a user. Can also be used as a reply, muting the replied to user.
❂ /zombies: searches deleted accounts
❂ /zombies clean: removes deleted accounts from the group.
❂ /snipe <chatid> <string>: Make me send a message to a specific chat.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_basic")]]
            ),
        )

    elif query.data == "lovelyx_disable":
        query.message.edit_text(
            text="""Here is the help for the Disabling module:

❂ /cmds: check the current status of *disabled* commands

*Admins only:*

❂ /enable <cmd name>: enable that command
❂ /disable <cmd name>: disable that command
❂ /enablemodule <module name>: enable all commands in that module
❂ /disablemodule <module name>: disable all commands in that module
❂ /listcmds: list all possible toggleable commands""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_basic")]]
            ),
        )

    elif query.data == "lovelyx_fsubfed":
        query.message.edit_text(
            text="""Here is the help for the F-Sub/Feds module:

*Force Subscribe:*

❂ Lovely can mute members who are not subscribed your channel until they subscribe
❂ When enabled I will mute unsubscribed members and show them a unmute button. When they pressed the button I will unmute them
❂Setup
Only creator
❂ Add me in your group as admin
❂ Add me in your channel as admin 
 
Commmands
❂ /fsub {channel username} - To turn on and setup the channel.

  💡Do this first...

❂ /fsub - To get the current settings.
❂ /fsub disable - To turn of ForceSubscribe..

  💡If you disable fsub, you need to set again for working.. /fsub {channel username} 

❂ /fsub clear - To unmute all members who muted by me.

*Federation*
Everything is fun, until a spammer starts entering your group, and you have to block it. Then you need to start banning more, and more, and it hurts.
But then you have many groups, and you don't want this spammer to be in one of your groups - how can you deal? Do you have to manually block it, in all your groups?

No longer! With Federation, you can make a ban in one chat overlap with all other chats.

You can even designate federation admins, so your trusted admin can ban all the spammers from chats you want to protect.

*Commands:*

Feds are now divided into 3 sections for your ease.
• `/fedownerhelp`: Provides help for fed creation and owner only commands
• `/fedadminhelp`: Provides help for fed administration commands
• `/feduserhelp`: Provides help for commands anyone can use""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_basic")]]
            ),
        )

    elif query.data == "lovelyx_blacklists":
        query.message.edit_text(
            text="""Here is the help for the Blacklists module:


Blacklists are used to stop certain triggers from being said in a group. Any time the trigger is mentioned, the message will immediately be deleted. A good combo is sometimes to pair this up with warn filters!

*NOTE: Blacklists do not affect group admins.*

❂ /blacklist: View the current blacklisted words.

*Admin only:*
❂ /addblacklist <triggers>: Add a trigger to the blacklist. Each line is considered one trigger, so using different lines will allow you to add multiple triggers.
❂ /unblacklist <triggers>: Remove triggers from the blacklist. Same newline logic applies here, so you can remove multiple triggers at once.
❂ /blacklistmode <off/del/warn/ban/kick/mute/tban/tmute>: Action to perform when someone sends blacklisted words.

Blacklist sticker is used to stop certain stickers. Whenever a sticker is sent, the message will be deleted immediately.
NOTE: Blacklist stickers do not affect the group admin
❂ /blsticker: See current blacklisted sticker
Only admin:
❂ /addblsticker <sticker link>: Add the sticker trigger to the black list. Can be added via reply sticker
❂ /unblsticker <sticker link>: Remove triggers from blacklist. The same newline logic applies here, so you can delete multiple triggers at once
❂ /rmblsticker <sticker link>: Same as above
❂ /blstickermode <delete/ban/tban/mute/tmute>: sets up a default action on what to do if users use blacklisted stickers
Note:
❂ <sticker link> can be `https://t.me/addstickers/<sticker> or just <sticker>` or reply to the sticker message""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_basic")]]
            ),
        )

    elif query.data == "lovelyx_filters":
        query.message.edit_text(
            text="""Here is the help for the Filters module:

❂ /filters*:* List all active filters saved in the chat.
*Admin only:*
❂ /filter <keyword> <reply message>*:* Add a filter to this chat. The bot will now reply that message whenever 'keyword'\
is mentioned. If you reply to a sticker with a keyword, the bot will reply with that sticker. NOTE: all filter \
keywords are in lowercase. If you want your keyword to be a sentence, use quotes. eg: /filter "hey there" How you \
doin?
 Separate diff replies by `%%%` to get random replies
 *Example:* 
 `/filter "filtername"
 Reply 1
 %%%
 Reply 2
 %%%
 Reply 3`
❂ /stop <filter keyword>*:* Stop that filter.
*Chat creator only:*
❂ /removeallfilters*:* Remove all chat filters at once.
*Note*: Filters also support markdown formatters like: {first}, {last} etc.. and buttons.
Check /markdownhelp to know more!""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_basic")]]
            ),
        )
#🔥🔥🔥🔥🔥🔥
    elif query.data == "lovelyx_basic":
        query.message.edit_text(
            text="""This are some *Basic commands* which will help you to manage group easily by Lovely""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Admins", callback_data="lovelyx_admin"),
                    InlineKeyboardButton(text="Bans/mute", callback_data="lovelyx_bansmute"),
                    InlineKeyboardButton(text="Disabling", callback_data="lovelyx_disable"),
                 ],      
                 [
                    InlineKeyboardButton(text="Filters", callback_data="lovelyx_filters"),
                    InlineKeyboardButton(text="Fsub/Feds", callback_data="lovelyx_fsubfed"),
                    InlineKeyboardButton(text="Greetings", callback_data="lovelyx_greetings"),
                 ],
                 [
                    InlineKeyboardButton(text="Group", callback_data="lovelyx_group"),
                    InlineKeyboardButton(text="Locks", callback_data="lovelyx_locks"),
                    InlineKeyboardButton(text="Rules", callback_data="lovelyx_rules"),
                 ],
                 [
                    InlineKeyboardButton(text="Advance", callback_data="lovelyx_advance"),
                    InlineKeyboardButton(text="Go Back", callback_data="emiko_"),
                    InlineKeyboardButton(text="Fun & Extra", callback_data="lovelyx_fe"),
                 ]
                ]
            ),
        )

    elif query.data == "lovelyx_greetings":
        query.message.edit_text(
            text="""Here is the help for the *Greetings* module:

*Admins only:*
❂ /welcome <on/off>: enable/disable welcome messages.
❂ /welcome: shows current welcome settings.
❂ /welcome noformat: shows current welcome settings, without the formatting - useful to recycle your welcome messages!
❂ /goodbye: same usage and args as /welcome.
❂ /setwelcome <sometext>: set a custom welcome message. If used replying to media, uses that media.
❂ /setgoodbye <sometext>: set a custom goodbye message. If used replying to media, uses that media.
❂ /resetwelcome: reset to the default welcome message.
❂ /resetgoodbye: reset to the default goodbye message.
❂ /cleanwelcome <on/off>: On new member, try to delete the previous welcome message to avoid spamming the chat.
❂ /welcomemutehelp: gives information about welcome mutes.
❂ /cleanservice <on/off: deletes telegrams welcome/left service messages.
 Example:
user joined chat, user left chat.
Welcome markdown:
❂ /welcomehelp: view more formatting information for custom welcome/goodbye messages.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_basic")]]
            ),
        )

    elif query.data == "lovelyx_group":
        query.message.edit_text(
            text="""Here is the help for the *Group* module:

*Admins only:*
❂ /setgtitle <text>: set group title
❂ /setgpic: reply to an image to set as group photo
❂ /setdesc: Set group description
❂ /setsticker: Set group sticker""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_basic")]]
            ),
        )

    elif query.data == "lovelyx_locks":
        query.message.edit_text(
            text="""Here is the help for the *Locks* module:

Do stickers annoy you? or want to avoid people sharing links? or pictures? You're in the right place!
The locks module allows you to lock away some common items in the telegram world; the bot will automatically delete them!

❂ /locktypes: Lists all possible locktypes

*Admins only:*

❂ /lock <type>: Lock items of a certain type (not available in private)
❂ /unlock <type>: Unlock items of a certain type (not available in private)
❂ /locks: The current list of locks in this chat.

Locks can be used to restrict a group's users.
eg:
Locking urls will auto-delete all messages with urls, locking stickers will restrict all non-admin users from sending stickers, etc.
Locking bots will stop non-admins from adding bots to the chat.

*Note:*
❂ Unlocking permission info will allow members (non-admins) to change the group information, such as the description or the group name
❂ Unlocking permission pin will allow members (non-admins) to pinned a message in a group""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_basic")]]
            ),
        )

    elif query.data == "lovelyx_rules":
        query.message.edit_text(
            text="""Here is the help for the *Rules* module:
*Rules:*
❂ /rules: get the rules for this chat.
❂ /setrules <your rules here>: set the rules for this chat.
❂ /clearrules: clear the rules for this chat.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_basic")]]
            ),
        )

    elif query.data == "lovelyx_tagalert":
        query.message.edit_text(
            text="""Here is help for the *Tagalert* module:

If anyone tagged/mentioned in a group where Lovely is present
Lovely will notify it to you in private message after enabling tag alerts

*How to use this feature ?*
❂ `/tagalert on` : Turn tag alerts on
❂ `/tagalert off` : Turn tag alerts off""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_advance")]]
            ),
        )

    elif query.data == "lovelyx_logo":
        query.message.edit_text(
            text="""Here is the help for the *Logomaker* module:
 This is help menu for logomaker

❂ /logo <text/name> - Create a logo with random view.
❂ /wlogo <text/name> - Create a logo with wide view only.

 Image Editor :

❂  /edit <reply photo> - to edit image.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_advance")]]
            ),
        )

    elif query.data == "lovelyx_search":
        query.message.edit_text(
            text="""Here is the help for the *Search* module:

❂ /google <query>: Perform a google search
❂ /image <query>: Search Google for images and returns them
For greater no. of results specify lim, For eg: /img hello lim=10
❂ /app <appname>: Searches for an app in Play Store and returns its details.
❂ /reverse: Does a reverse image search of the media which it was replied to.
❂ /gps <location>: Get gps location.
❂ /github <username>: Get information about a GitHub user.
❂ /country <country name>: Gathering info about given country
❂ /imdb <Movie name>: Get full info about a movie with imdb.com""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_advance")]]
            ),
        )

    elif query.data == "lovelyx_logch":
        query.message.edit_text(
            text="""Here is the help for the *Log Channel​* module:

  *Log channel*

❂ /logchannel: get log channel info
❂ /setlog: set the log channel.
❂ /unsetlog: unset the log channel.

Setting the log channel is done by:

➩ adding the bot to the desired channel (as an admin!)
➩ sending /setlog in the channel
➩ forwarding the /setlog to the group""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_advance")]]
            ),
        )

    elif query.data == "lovelyx_trans":
        query.message.edit_text(
            text="""Here is the help for the Translator module:
 
Use this module to translate stuff!
Commands:
❂ /tl (or /tr): as a reply to a message, translates it to English.
❂ /tl <lang>: translates to <lang>
eg: /tl ja: translates to Japanese.
❂ /tl <source>//<dest>: translates from <source> to <lang>.
eg:  /tl ja//en: translates from Japanese to English.
❂ /langs: get a list of supported languages for translation.

I can convert text to voice and voice to text..
❂ /tts <lang code>: Reply to any message to get text to speech output
❂ /stt: Type in reply to a voice message(support english only) to extract text from it.
Language Codes
`af,am,ar,az,be,bg,bn,bs,ca,ceb,co,cs,cy,da,de,el,en,eo,es,
et,eu,fa,fi,fr,fy,ga,gd,gl,gu,ha,haw,hi,hmn,hr,ht,hu,hy,
id,ig,is,it,iw,ja,jw,ka,kk,km,kn,ko,ku,ky,la,lb,lo,lt,lv,mg,mi,mk,
ml,mn,mr,ms,mt,my,ne,nl,no,ny,pa,pl,ps,pt,ro,ru,sd,si,sk,sl,
sm,sn,so,sq,sr,st,su,sv,sw,ta,te,tg,th,tl,tr,uk,ur,uz,
vi,xh,yi,yo,zh,zh_CN,zh_TW,zu`""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_advance")]]
            ),
        )

    elif query.data == "lovelyx_advance":
        query.message.edit_text(
            text="""*Advanced commands*
Advanced commands will help you to secure your group easily and also you will know here some awesome features""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Logomaker", callback_data="lovelyx_logo"),
                    InlineKeyboardButton(text="Log channels", callback_data="lovelyx_logch"),
                    InlineKeyboardButton(text="Search", callback_data="lovelyx_search"),
                 ],      
                 [
                    InlineKeyboardButton(text="Tagalert", callback_data="lovelyx_tagalert"),   
                    InlineKeyboardButton(text="Translator", callback_data="lovelyx_trans"),
                 ],
                 [
                    InlineKeyboardButton(text="Basic", callback_data="lovelyx_basic"),
                    InlineKeyboardButton(text="Go Back", callback_data="emiko_"),
                    InlineKeyboardButton(text="Fun & Extra", callback_data="lovelyx_fe"),
                 ]
                ]
            ),
        )

    elif query.data == "lovelyx_info":
        query.message.edit_text(
            text="""Here is the help for the *Info* module:

ID:
❂ /id: get the current group id. If used by replying to a message, gets that user's id.
❂ /gifid: reply to a gif to me to tell you its file ID.
 
Self addded information: 
❂ /setme <text>: will set your info
❂ /me: will get your or another user's info.
Examples:
❂ /setme I am a wolf.
❂ /me @username(defaults to yours if no user specified)
 
Information others add on you: 
❂ /bio: will get your or another user's bio. This cannot be set by yourself.
❂ /setbio <text>: while replying, will save another user's bio 
Examples:
❂ /bio @username(defaults to yours if not specified).
❂ /setbio This user is a wolf (reply to the user)
 
Overall Information about you:
❂ /info: get information about a user. 
 
json Detailed info:
❂ /json: Get Detailed info about any message.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_extras":
        query.message.edit_text(
            text="""Here is the help for the "Extras* module:

*Available commands:*

❂ /markdownhelp: quick summary of how markdown works in telegram - can only be called in private chats
❂ /paste: Saves replied content to nekobin.com and replies with a url
❂ /react: Reacts with a random reaction 
❂ /ud <word>: Type the word or expression you want to search use
❂ /reverse: Does a reverse image search of the media which it was replied to.
❂ /wiki <query>: wikipedia your query
❂ /wall <query>: get a wallpaper from wall.alphacoders.com
❂ /cash: currency converter
 Example:
 `/cash 1 USD INR  
      OR
 /cash 1 usd inr
 Output: 1.0 USD = 75.505 INR`""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_sangmata":
        query.message.edit_text(
            text="""Here is the help for *Sangmata Info* module:
❂ /sg <reply>: To check history name""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_telegraph":
        query.message.edit_text(
            text="""Here is the help for the *Telegraph* module:

❂ /tgm : Get Telegraph Link Of Replied Media
❂ /tgt: Get Telegraph Link of Replied Text""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_weather":
        query.message.edit_text(
            text="""Here is help for *Weather* module: 
Date-time-Weather
❂ /time <country code>: Gives information about a timezone.
❂ /weather <city>: Get weather info in a particular place.
❂ /wttr <city>: Advanced weather module, usage same as /weather
❂ /wttr moon: Get the current status of moon""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_fun":
        query.message.edit_text(
            text="""Here is the help for the *Fun* module:

❂ /runs: reply a random string from an array of replies
❂ /slap: slap a user, or get slapped if not a reply
❂ /shrug: get shrug XD
❂ /table: get flip/unflip :v
❂ /decide: Randomly answers yes/no/maybe
❂ /toss: Tosses A coin
❂ /bluetext: check urself :V
❂ /roll: Roll a dice
❂ /rlg: Join ears,nose,mouth and create an emo ;-;
❂ /shout <keyword>: write anything you want to give loud shout
❂ /weebify <text>: returns a weebified text
❂ /sanitize: always use this before /pat or any contact
❂ /pat: pats a user, or get patted
❂ /8ball: predicts using 8ball method

- Animation
❂ /love 
❂ /hack 
❂ /bombs 

*Couples*
❂ /couples - get couples of today

*- Here is the help for the Styletext module:*

❂ /weebify <text>: weebify your text!
❂ /bubble <text>: bubble your text!
❂ /fbubble <text>: bubble-filled your text!
❂ /square <text>: square your text!
❂ /fsquare <text>: square-filled your text!
❂ /blue <text>: bluify your text!
❂ /latin <text>: latinify your text!
❂ /lined <text>: lined your text!""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_style":
        query.message.edit_text(
            text="""Here is the help for the *Styletext* module:

❂ /weebify <text>: weebify your text!
❂ /bubble <text>: bubble your text!
❂ /fbubble <text>: bubble-filled your text!
❂ /square <text>: square your text!
❂ /fsquare <text>: square-filled your text!
❂ /blue <text>: bluify your text!
❂ /latin <text>: latinify your text!
❂ /lined <text>: lined your text!""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_ani":
        query.message.edit_text(
            text="""Here is the help for the *Animation* module

*Commands*
❂ /love 
❂ /hack 
❂ /bombs """,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_couples":
        query.message.edit_text(
            text="""Here is the help for the *Couples* module

*Commands*
❂ /couples - get couples of today""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_anime":
        query.message.edit_text(
            text="""Here is the help for the Anime module:

  *Anime search*                         
❂ /anime <anime>: returns information about the anime.
❂ /whatanime: returns source of anime when replied to photo or gif.                                                          
❂ /character <character>: returns information about the character.
❂ /manga <manga>: returns information about the manga.
❂ /user <user>: returns information about a MyAnimeList user.
❂ /upcoming: returns a list of new anime in the upcoming seasons.
❂ /airing <anime>: returns anime airing info.
❂ /whatanime <anime>: reply to gif or photo.
❂ /kaizoku <anime>: search an anime on animekaizoku.com
❂ /kayo <anime>: search an anime on animekayo.com

  *Anime Quotes*
❂ /animequotes: for anime quotes randomly as photos.
❂ /quote: send quotes randomly as text""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_hht":
        query.message.edit_text(
            text="""hh
H""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )

    elif query.data == "lovelyx_afk":
        query.message.edit_text(
            text="""Here is the help for *Afk* module:

*Commands:*
When marked as AFK, any mentions will be replied to with a message stating that you're not available!
❂ /afk <reason>: Mark yourself as AFK.
  - brb <reason>: Same as the afk command, but not a command. """,
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_fe")]]
            ),
        )


    elif query.data == "lovelyx_fe":
        query.message.edit_text(
            text="""Fun tools and Extras
Extra tools which are available in bot and tools made for fun are here
You can choose an option below, by clicking a button.
For any query join @LOVELYAPPEAL""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Afk", callback_data="lovelyx_afk"),
                    InlineKeyboardButton(text="Anime", callback_data="lovelyx_anime"),
                    InlineKeyboardButton(text="Animation", callback_data="lovelyx_ani"),
                 ],      
                 [
                    InlineKeyboardButton(text="Couples", callback_data="lovelyx_couples"),
                    InlineKeyboardButton(text="Extras", callback_data="lovelyx_extras"),
                    InlineKeyboardButton(text="Fun", callback_data="lovelyx_fun"),
                 ],
                 [
                    InlineKeyboardButton(text="Info", callback_data="lovelyx_info"),
                    InlineKeyboardButton(text="Sangmata", callback_data="lovelyx_sangmata"),
                    InlineKeyboardButton(text="Styletext", callback_data="lovelyx_style"),
                 ],
                 [
                    InlineKeyboardButton(text="Weather", callback_data="lovelyx_weather"), 
                    InlineKeyboardButton(text="Telegraph", callback_data="lovelyx_telegraph"),
                 ],
                 [
                    InlineKeyboardButton(text="Advance", callback_data="lovelyx_advance"),
                    InlineKeyboardButton(text="Back", callback_data="emiko_"),
                    InlineKeyboardButton(text="Basic", callback_data="lovelyx_basic"),
                 ]
                ]
            ),
        )

#🤣🤣🤣🤣

def get_help(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    args = update.effective_message.text.split(None, 1)

    # ONLY send help in PM
    if chat.type != chat.PRIVATE:
        if len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
            module = args[1].lower()
            update.effective_message.reply_text(
                f"Contact me in PM to get help of {module.capitalize()}",
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Help",
                                url="t.me/{}?start=ghelp_{}".format(
                                    context.bot.username, module
                                ),
                            )
                        ]
                    ]
                ),
            )

            return
        update.effective_message.reply_text(
            "Use below buttons to explore my awesome features in pm or group.",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Open in private chat",
                            url="t.me/{}?start=help".format(context.bot.username),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            text="Open here", callback_data="help_back"
                        ),
                    ],
                ]
            ),
        )
        return

    elif len(args) >= 2 and any(args[1].lower() == x for x in HELPABLE):
        module = args[1].lower()
        text = (
            "Here is the available help for the *{}* module:\n".format(
                HELPABLE[module].__mod_name__
            )
            + HELPABLE[module].__help__
        )
        send_help(
            chat.id,
            text,
            InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Go Back", callback_data="help_back")]]
            ),
        )

    else:
        send_help(chat.id, LOVELY_HELP)


def send_settings(chat_id, user_id, user=False):
    if user:
        if USER_SETTINGS:
            settings = "\n\n".join(
                "*{}*:\n{}".format(mod.__mod_name__, mod.__user_settings__(user_id))
                for mod in USER_SETTINGS.values()
            )
            dispatcher.bot.send_message(
                user_id,
                "These are your current settings:" + "\n\n" + settings,
                parse_mode=ParseMode.MARKDOWN,
            )

        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any user specific settings available :'(",
                parse_mode=ParseMode.MARKDOWN,
            )

    else:
        if CHAT_SETTINGS:
            chat_name = dispatcher.bot.getChat(chat_id).title
            dispatcher.bot.send_message(
                user_id,
                text="Which module would you like to check {}'s settings for?".format(
                    chat_name
                ),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )
        else:
            dispatcher.bot.send_message(
                user_id,
                "Seems like there aren't any chat settings available :'(\nSend this "
                "in a group chat you're admin in to find its current settings!",
                parse_mode=ParseMode.MARKDOWN,
            )


def settings_button(update: Update, context: CallbackContext):
    query = update.callback_query
    user = update.effective_user
    bot = context.bot
    mod_match = re.match(r"stngs_module\((.+?),(.+?)\)", query.data)
    prev_match = re.match(r"stngs_prev\((.+?),(.+?)\)", query.data)
    next_match = re.match(r"stngs_next\((.+?),(.+?)\)", query.data)
    back_match = re.match(r"stngs_back\((.+?)\)", query.data)
    try:
        if mod_match:
            chat_id = mod_match.group(1)
            module = mod_match.group(2)
            chat = bot.get_chat(chat_id)
            text = "*{}* has the following settings for the *{}* module:\n\n".format(
                escape_markdown(chat.title), CHAT_SETTINGS[module].__mod_name__
            ) + CHAT_SETTINGS[module].__chat_settings__(chat_id, user.id)
            query.message.reply_text(
                text=text,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    [
                        [
                            InlineKeyboardButton(
                                text="Go Back",
                                callback_data="stngs_back({})".format(chat_id),
                            )
                        ]
                    ]
                ),
            )

        elif prev_match:
            chat_id = prev_match.group(1)
            curr_page = int(prev_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        curr_page - 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif next_match:
            chat_id = next_match.group(1)
            next_page = int(next_match.group(2))
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                "Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(chat.title),
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(
                        next_page + 1, CHAT_SETTINGS, "stngs", chat=chat_id
                    )
                ),
            )

        elif back_match:
            chat_id = back_match.group(1)
            chat = bot.get_chat(chat_id)
            query.message.reply_text(
                text="Hi there! There are quite a few settings for {} - go ahead and pick what "
                "you're interested in.".format(escape_markdown(chat.title)),
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(0, CHAT_SETTINGS, "stngs", chat=chat_id)
                ),
            )

        # ensure no spinny white circle
        bot.answer_callback_query(query.id)
        query.message.delete()
    except BadRequest as excp:
        if excp.message not in [
            "Message is not modified",
            "Query_id_invalid",
            "Message can't be deleted",
        ]:
            LOGGER.exception("Exception in settings buttons. %s", str(query.data))


def get_settings(update: Update, context: CallbackContext):
    chat = update.effective_chat  # type: Optional[Chat]
    user = update.effective_user  # type: Optional[User]
    msg = update.effective_message  # type: Optional[Message]

    # ONLY send settings in PM
    if chat.type != chat.PRIVATE:
        if is_user_admin(chat, user.id):
            text = "Click here to get this chat's settings, as well as yours."
            msg.reply_text(
                text,
                reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(
                            text="Open in private chat",
                                url="t.me/{}?start=stngs_{}".format(
                                    context.bot.username, chat.id)
                        ),
                    ],
                    [
                        InlineKeyboardButton(
                           text="Close", callback_data="stngs_back"
                        ),
                    ]
                ]
            ),
        )
        else:
            text = "Click here to check your settings."

    else:
        send_settings(chat.id, user.id, True)


def donate(update: Update, context: CallbackContext):
    user = update.effective_message.from_user
    chat = update.effective_chat  # type: Optional[Chat]
    bot = context.bot
    if chat.type == "private":
        update.effective_message.reply_text(
            DONATE_STRING, parse_mode=ParseMode.MARKDOWN, disable_web_page_preview=True
        )

        if OWNER_ID != 1669178360:
            update.effective_message.reply_text(
                "I'm free for everyone ❤️ If you wanna make me smile, just join"
                "[My Channel]({})".format(DONATION_LINK),
                parse_mode=ParseMode.MARKDOWN,
            )
    else:
        try:
            bot.send_message(
                user.id,
                DONATE_STRING,
                parse_mode=ParseMode.MARKDOWN,
                disable_web_page_preview=True,
            )

            update.effective_message.reply_text(
                "I've PM'ed you about donating to my creator!"
            )
        except Unauthorized:
            update.effective_message.reply_text(
                "Contact me in PM first to get donation information."
            )


def migrate_chats(update: Update, context: CallbackContext):
    msg = update.effective_message  # type: Optional[Message]
    if msg.migrate_to_chat_id:
        old_chat = update.effective_chat.id
        new_chat = msg.migrate_to_chat_id
    elif msg.migrate_from_chat_id:
        old_chat = msg.migrate_from_chat_id
        new_chat = update.effective_chat.id
    else:
        return

    LOGGER.info("Migrating from %s, to %s", str(old_chat), str(new_chat))
    for mod in MIGRATEABLE:
        mod.__migrate__(old_chat, new_chat)

    LOGGER.info("Successfully migrated!")
    raise DispatcherHandlerStop


def main():

    if SUPPORT_CHAT is not None and isinstance(SUPPORT_CHAT, str):
        try:
            dispatcher.bot.sendMessage(
                f"@{SUPPORT_CHAT}", 
                f"""**Jai hind 🇮🇳**

**Python:** `{memek()}`
**Telegram Library:** `v{peler}`""",
                parse_mode=ParseMode.MARKDOWN
            )
        except Unauthorized:
            LOGGER.warning(
                "Bot isnt able to send message to support_chat, go and check!"
            )
        except BadRequest as e:
            LOGGER.warning(e.message)

    test_handler = CommandHandler("test", test, run_async=True)
    start_handler = CommandHandler("start", start, run_async=True)

    help_handler = CommandHandler("help", get_help, run_async=True)
    help_callback_handler = CallbackQueryHandler(
        help_button, pattern=r"help_.*", run_async=True
    )

    lovelybasic_handler = CommandHandler("lovelybasic", test, run_async=True)
    lovelybasic_callback_handler = CallbackQueryHandler(
        lovelybasic_button, pattern=r"lovelybasic_.*", run_async=True
    )

    settings_handler = CommandHandler("settings", get_settings, run_async=True)
    settings_callback_handler = CallbackQueryHandler(
        settings_button, pattern=r"stngs_", run_async=True
    )

    about_callback_handler = CallbackQueryHandler(
        emiko_about_callback, pattern=r"emiko_", run_async=True
    )

    lovelyx_callback_handler = CallbackQueryHandler(
        lovelyx_about_callback, pattern=r"lovelyx_", run_async=True
    )

    donate_handler = CommandHandler("donate", donate, run_async=True)
    migrate_handler = MessageHandler(
        Filters.status_update.migrate, migrate_chats, run_async=True
    )

    dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(lovelybasic_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(lovelyx_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
    dispatcher.add_handler(lovelybasic_callback_handler)
    dispatcher.add_handler(settings_callback_handler)
    dispatcher.add_handler(migrate_handler)
    dispatcher.add_handler(donate_handler)

    dispatcher.add_error_handler(error_callback)

    if WEBHOOK:
        LOGGER.info("Using webhooks.")
        updater.start_webhook(listen="0.0.0.0", port=PORT, url_path=TOKEN)

        if CERT_PATH:
            updater.bot.set_webhook(url=URL + TOKEN, certificate=open(CERT_PATH, "rb"))
        else:
            updater.bot.set_webhook(url=URL + TOKEN)

    else:
        LOGGER.info("Using long polling.")
        updater.start_polling(timeout=15, read_latency=4, drop_pending_updates=True)

    if len(argv) not in (1, 3, 4):
        telethn.disconnect()
    else:
        telethn.run_until_disconnected()

    updater.idle()


if __name__ == "__main__":
    LOGGER.info("Successfully loaded modules: " + str(ALL_MODULES))
    telethn.start(bot_token=TOKEN)
    pbot.start()
    main()
