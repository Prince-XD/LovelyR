from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ParseMode, Update
from telegram.ext import (
    CallbackContext,
    CallbackQueryHandler,
    CommandHandler,
    Filters,
    MessageHandler,
)
from Zaid import dispatcher

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


def lovelyx_about_callback(update, context):
    query = update.callback_query
    if query.data == "lovelyx_":
        query.message.edit_text(
__help__ = """
Here is the info about *Formatting* module:

supports a large number of formatting options to make your messages more expressive. Take a look!
""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
              [
                [InlineKeyboardButton(text="Markdown", callback_data="lovelyx_ma"),
                 InlineKeyboardButton(text="filling", callback_data="lovelyx_fill")]
                ]
            ),
        )              

    elif query.data == "lovelyx_ma":
        query.message.edit_text(
            text="""*Markdown Formatting*
  You can format your message using *bold*, _italics_, -underline-, and much more. Go ahead and experiment!
  Supported markdown:
  - ``code words``: Backticks are used for monospace fonts. Shows as: code words.
  - `_italic words_`: Underscores are used for italic fonts. Shows as: italic words.
  - `*bold words*`: Asterisks are used for bold fonts. Shows as: bold words.
  - `~strikethrough~`: Tildes are used for strikethrough. Shows as: strikethrough.
  - `[hyperlink](example.com)`: This is the formatting used for hyperlinks. Shows as: hyperlink.
  - `[My Button](buttonurl://example.com)`: This is the formatting used for creating buttons. This example will create a button named "My button" which opens example.com when clicked.
  If you would like to send buttons on the same row, use the :same formatting.
  Example:
  `[button 1](buttonurl://example.com)`
  `[button 2](buttonurl://example.com:same)`
  `[button 3](buttonurl://example.com)`
  This will show button 1 and 2 on the same line, with 3 underneath.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_")]]
            ),
        )

    elif query.data == "lovelyx_fill":
        query.message.edit_text(
            text="""*Fillings*
You can also customise the contents of your message with contextual data. For example, you could mention a user by name in the welcome message, or mention them in a filter!
You can use these to mention a user in notes too!
Supported fillings:
- `{first}`: The user's first name.
- `{last}`: The user's last name.
- `{fullname}`: The user's full name.
- `{username}`: The user's username. If they don't have one, mentions the user instead.
- `{mention}`: Mentions the user with their firstname.
- `{id}`: The user's ID.
- `{chatname}`: The chat's name.""",
            parse_mode=ParseMode.MARKDOWN,
            disable_web_page_preview=True,
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton(text="Back", callback_data="lovelyx_")]]
            ),
        )

__mod_name__ = "Formatting"

    CallbackQueryHandler(
        lovelyx_about_callback, pattern=r"lovelyx_", run_async=True
    )

    dispatcher.add_handler(lovelyx_callback_handler)
