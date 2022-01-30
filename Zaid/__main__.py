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


PM_START_TEXT = """
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

buttons = [
     [
        InlineKeyboardButton(text="Add Lovely", url="https://t.me/LOVELYR_OBOT?startgroup=true"),
        InlineKeyboardButton(text="About", callback_data="lovelyx_"),
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


HELP_STRINGS = """
༆*Lovely comes with many special features in it*༆
꧁*check all button below to explore every commands of lovely*꧂
𖣘 *All commands can either be used with* `/` *or* `!`.
𖣘 *If you facing any issue or find any bugs in any command then you can report it in @LOVELYAPPEAL* .
"""

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
                PM_START_TEXT.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),                        
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
            )
    else:
        update.effective_message.reply_text(
            "I'm Lovely group management/Music bot."
            "\n\n I can do a variety of things, most common of em are:"
            "\n- Restrict users with ban permissions."
            "\n- Greet users with media + text and buttons, with proper formatting."
            "\n- Restrict users who flood your chat using my anti-flood module."
            "\n- Warn users according to the options set and restrict em accordingly."
            "\n- Save notes and filters with proper formatting and reply markup."
            "\n- I can also Play Music in groups"
            "\n\n Theres even more! this is just the tip of the iceberg. Do note I need"
            "\n to be promoted with proper admin permissions to function properly." 
            "\n Else I won't be able to function as said."
            "\n\n Click on help to learn more and Join @Lovelyappeal for report bugs!",
            parse_mode=ParseMode.MARKDOWN,
            reply_markup=InlineKeyboardMarkup(
[
     [
        InlineKeyboardButton(text="Add Lovely", url="https://t.me/LOVELYR_OBOT?startgroup=true"),
        InlineKeyboardButton(text="About", callback_data="lovelyx_"),
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
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(curr_page - 1, HELPABLE, "help")
                ),
            )

        elif next_match:
            next_page = int(next_match.group(1))
            query.message.edit_text(
                text=HELP_STRINGS,
                parse_mode=ParseMode.MARKDOWN,
                reply_markup=InlineKeyboardMarkup(
                    paginate_modules(next_page + 1, HELPABLE, "help")
                ),
            )

        elif back_match:
            query.message.edit_text(
                text=HELP_STRINGS,
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


def emiko_about_callback(update, context):
    query = update.callback_query
    if query.data == "emiko_":
        query.message.edit_text(
       text="I'm Lovely, a powerful group management bot built to help you manage your group easily."
            "\n• I can restrict users."
            "\n• I can greet users with customizable welcome messages and even set a group's rules."
            "\n• I have an advanced anti-flood system."
            "\n• I can warn users until they reach max warns, with each predefined actions such as ban, mute, kick, etc."
            "\n• I have a note keeping system, blacklists, and even predetermined replies on certain keywords."
            "\n• I check for admins' permissions before executing any command and more stuffs"
            "\n\n_ licensed under the GNU General Public License v3.0_"
            "\n\n Click on button bellow to get basic help.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Basic Commands", callback_data="emiko_admin"),
                    InlineKeyboardButton(text="Advanced Commands", callback_data="emiko_support"),
                 ],      
                 [
                    InlineKeyboardButton(text="Fun and extra", callback_data="emiko_credit"),
                    InlineKeyboardButton(text="Inline", switch_inline_query_current_chat=""),
                 ],
                 [
                    InlineKeyboardButton(text="All Commands", callback_data="help_back"),
                 ],
                 [
                    InlineKeyboardButton(text="Go Back", callback_data="emiko_back"),
                 ]
                ]
            ),
        )
    elif query.data == "emiko_back":
        first_name = update.effective_user.first_name
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_text(
                PM_START_TEXT.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

    elif query.data == "emiko_admin":
        query.message.edit_text(
            text="❂ /ban <userhandle>: bans a user. (via handle, or reply)"
                 "\n ❂ /unban <userhandle>: unbans a user. (via handle, or reply)"
                 "\n❂ /mute <userhandle>: silences a user. Can also be used as a reply, muting the replied to user."
                 "\n❂ /unmute <userhandle>: unmutes a user. Can also be used as a reply, muting the replied to user."
                 "\n\n❂ /promote: promotes the user replied to"
                 "\n❂ /fullpromote: promotes the user replied to with full rights"
                 "\n❂ /demote: demotes the user replied to"
                 "\n❂ /title <title here>: sets a custom title for an admin that the bot promoted"
                 "\n❂ /admincache: refresh the admins list"
                 "\n❂ /pin: silently pins the message replied to - add 'loud' or 'notify' to give notifs to users"
                 "\n❂ /unpin: unpins the currently pinned message"
                 "\n❂ /invitelink: gets invitelink"
                 "\n❂ /purge: deletes all messages between this and the replied to message."
                 "\n\n**Rules:**"
                 "\n❂ /rules: get the rules for this chat."
                 "\n❂ /setrules <your rules here>: set the rules for this chat."
                 "\n❂ /clearrules: clear the rules for this chat."
                 "\n❂ /filters: List all active filters saved in the chat."
                 "\n\n**Admin only:**"
                 "\n❂ /filter <keyword> <reply message>: Add a filter to this chat. The bot will now reply that message whenever 'keyword'is mentioned."
                 "\n\n❂ /stop <filter keyword>: Stop that filter."
                 "\n\n**Note:** Filters also support markdown formatters like: {first}, {last} etc.. and buttons."
                 "\nCheck /markdownhelp to know more!"
                 "\n\nOverall Information about you:"
                 "\n❂ /info: get information about a user."
                 "\n\njson Detailed info:"
                 "\n❂ /json: Get Detailed info about any message."
                 "\n\n**Welcome/Goodbye:**"
                 "\n❂ /welcome <on/off>: enable/disable welcome messages."
                 "\n❂ /welcome: shows current welcome settings."
                 "\n❂ /welcome noformat: shows current welcome settings, without the formatting - useful to recycle your welcome messages!"
                 "\n❂ /goodbye: same usage and args as /welcome."
                 "\n❂ /setwelcome <sometext>: set a custom welcome message. If used replying to media, uses that media."
                 "\n❂ /setgoodbye <sometext>: set a custom goodbye message. If used replying to media, uses that media."
                 "\n❂ /resetwelcome: reset to the default welcome message."
                 "\n❂ /resetgoodbye: reset to the default goodbye",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Go Back", callback_data="emiko_")]]
            ),
        )

    elif query.data == "emiko_support":
        query.message.edit_text(
            text="\n❂ /admins: list of admins in the chat"
                 "\n❂ /pinned: to get the current pinned message"
                 "\n❂ /setgpic: reply to an image to set as group photo"
                 "\n❂ /setdesc: Set group description"
                 "\n❂ /setsticker: Set group sticker"
                 "\n\n❂ /animequotes: for anime quotes randomly as photos."
                 "\n❂ /quote: send quotes randomly as text"
                 "\n\n❂ /sban <userhandle>: Silently ban a user. Deletes command, Replied message and doesn't reply. (via handle, or reply)"
                 "\n❂ /tban <userhandle> x(m/h/d): bans a user for x time. (via handle, or reply). m = minutes, h = hours, d = days."
                 "\n❂ /tmute <userhandle> x(m/h/d): mutes a user for x time. (via handle, or reply). m = minutes, h = hours, d = days."
                 "\n❂ /zombies: searches deleted accounts"
                 "\n❂ /zombies clean: removes deleted accounts from the group."
                 "\n❂ /snipe <chatid> <string>: Make me send a message to a specific chat."
                 "\n\n❂ /cleanwelcome <on/off>: On new member, try to delete the previous welcome message to avoid spamming the chat."
                 "\n❂ /welcomemutehelp: gives information about welcome mutes."
                 "\n❂ /cleanservice <on/off: deletes telegrams welcome/left service messages."
                 "\n\n**Example:**"
                 "\nuser joined chat, user left chat."
                 "\n\n**Welcome markdown:**"
                 "\n❂ /welcomehelp: view more formatting information for custom welcome/goodbye messages."
                 "\n\n❂ /logo <text/name> - Create a logo with random view."
                 "\n❂ /wlogo <text/name> - Create a logo with wide view only."
                 "\n\n**Image Editor :**"
                 "\n❂  /edit <reply photo> - to edit image.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Go Back", callback_data="emiko_")]]
            ),
        )

    elif query.data == "emiko_credit":
        query.message.edit_text(
            text="Fun And extra commands"
                 "\n\n❂ /logo <text/name> - Create a logo with random view."
                 "\n❂ /wlogo <text/name> - Create a logo with wide view only."
                 "\n\nImage Editor :"
                 "\n❂  /edit <reply photo> - to edit image."
                 "\n\nstickers tools"
                 "\n❂ /stickerid: reply to a sticker to me to tell you its file ID."
                 "\n❂ /getsticker: reply to a sticker to me to upload its raw PNG file."
                 "\n❂ /kang: reply to a sticker to add it to your pack."
                 "\n❂ /delsticker: Reply to your anime exist sticker to your pack to delete it."
                 "\n❂ /stickers: Find stickers for given term on combot sticker catalogue"
                 "\n❂ /tiny: To make small sticker"
                 "\n❂ /kamuii <1-8> : To deepefying stiker"
                 "\n❂ /mmf <reply with text>: To draw a text for sticker or pohots"
                 "\n\n❂ /runs: reply a random string from an array of replies"
                 "\n❂ /slap: slap a user, or get slapped if not a reply"
                 "\n❂ /shrug: get shrug XD"
                 "\n❂ /table: get flip/unflip :v"
                 "\n❂ /decide: Randomly answers yes/no/maybe"
                 "\n❂ /toss: Tosses A coin"
                 "\n❂ /bluetext: check urself :V"
                 "\n❂ /roll: Roll a dice"
                 "\n❂ /rlg: Join ears,nose,mouth and create an emo ;-;"
                 "\n❂ /shout <keyword>: write anything you want to give loud shout"
                 "\n❂ /weebify <text>: returns a weebified text"
                 "\n❂ /sanitize: always use this before /pat or any contact"
                 "\n❂ /pat: pats a user, or get patted"
                 "\n❂ /8ball: predicts using 8ball method"
                 "\n\n- Animation"
                 "\n❂ /love"
                 "\n❂ /hack"
                 "\n❂ /bombs"
                 "\n\n- Shippering"
                 "\n❂ /couples - get couples of today"
                 "\n\nMusic and video commands"
                 "\n❂ /video or /vsong (query): download video from youtube"
                 "\n❂ /music or /song (query): download song from yt servers. (API BASED)"
                 "\n❂ /lyrics (song name) : This plugin searches for song lyrics with song name.",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Go Back", callback_data="emiko_")]]
            ),
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
                    InlineKeyboardButton(text="Next", callback_data="emiko_back"),
                 ]
                ]
            ),
        )
    elif query.data == "lovelyx_back":
        first_name = update.effective_user.first_name
        uptime = get_readable_time((time.time() - StartTime))
        query.message.edit_text(
                PM_START_TEXT.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )
    elif query.data == "lovelyx_pro":
        query.message.edit_text(
            text="""<b>Hey, Welcome to Tiana configuration Tutorial
Before we go, I need admin permissions in this chat to work properly
1) Click Manage Group
2) Go to Administrators and add</b> @LOVELYR_OBOT <b>as Admin
3) Giving full permissions make Lovely fully useful</b>""",
            parse_mode=ParseMode.HTML,
            reply_markup=InlineKeyboardMarkup(
              [[InlineKeyboardButton(text="⬅️", callback_data="lovelyx_"),
                InlineKeyboardButton(text="➡️", callback_data="lovelyx_help")],               
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
                [InlineKeyboardButton(text="⬅️", callback_data="lovelyx_pro"),
                 InlineKeyboardButton(text="➡️", callback_data="emiko_back")]
                ]
            ),
        )


def source_about_callback(update, context):
    query = update.callback_query
    if query.data == "source_":
        query.message.edit_text(
            text="Ok well done"
                 "\n\nNow let me work correctly, you need to make me Admin of you Group!"
                 "\n\nTo do that, follow the step:)"
                 "\n\n•  Go to your group"
                 "\n•  Press the Group's name"
                 "\n•  Press Modify"
                 "\n•  Press on Administrator"
                 "\n•  Press Add Administrator"
                 "\n•  Press the Magnifying Glass"
                 "\n•  Search @LOVELYR_OBOT"
                 "\n• Confirm",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [
                 [
                    InlineKeyboardButton(text="Video Tutorial", url="https://t.me/LOVELY_ROBOTS/38https://t.me/LOVELY_ROBOTS/38"),
                 ],
                 [
                    InlineKeyboardButton(text="Done", callback_data="emiko_"),
                 ]
                ]
            ),
        )
    elif query.data == "source_back":
        first_name = update.effective_user.first_name
        query.message.edit_text(
                PM_START_TEXT.format(
                    escape_markdown(first_name),
                    escape_markdown(uptime),
                    sql.num_users(),
                    sql.num_chats()),
                reply_markup=InlineKeyboardMarkup(buttons),
                parse_mode=ParseMode.MARKDOWN,
                timeout=60,
                disable_web_page_preview=False,
        )

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
        send_help(chat.id, HELP_STRINGS)


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

    source_callback_handler = CallbackQueryHandler(
        source_about_callback, pattern=r"source_", run_async=True
    )

    donate_handler = CommandHandler("donate", donate, run_async=True)
    migrate_handler = MessageHandler(
        Filters.status_update.migrate, migrate_chats, run_async=True
    )

    dispatcher.add_handler(test_handler)
    dispatcher.add_handler(start_handler)
    dispatcher.add_handler(help_handler)
    dispatcher.add_handler(about_callback_handler)
    dispatcher.add_handler(lovelyx_callback_handler)
    dispatcher.add_handler(source_callback_handler)
    dispatcher.add_handler(settings_handler)
    dispatcher.add_handler(help_callback_handler)
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
