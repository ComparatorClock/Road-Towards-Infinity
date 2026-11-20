"""Road Towards Infinity - a clicker game about ever-bigger numbers.

Web edition: this whole file runs inside the browser through Pyodide (Python compiled to WebAssembly).
index.html is only a wrapper that loads Pyodide and then runs this file. Host both files in the same folder.
"""
import asyncio
import re
from types import SimpleNamespace
from typing import NamedTuple

import js
from js import document, window
from pyodide.ffi import create_once_callable, create_proxy, to_js
from pyodide.ffi.wrappers import clear_timeout, set_interval, set_timeout

# =====================================================================
# 0. SITE SETTINGS - edit these
# =====================================================================

# Where the images live. Expected inside: icon.png, spacer.png, backgrounds/<theme>.png (incl. default.png and shader.png)
ASSET_BASE = "https://file.garden/ZADcT1kUN2HXG_qX/RoadTowardsInfinity/"

# Pop-up shown every time the site loads, explaining the save cookie. HTML is allowed in the text.
COOKIE_NOTICE_TITLE = "NOTICE: This Site Uses One Cookie"
COOKIE_NOTICE_TEXT = "This site uses exactly one cookie - it is for your save-states. It is not used for any data tracking or harvesting purposes, and you can even check and modify the cookie yourself if you so desire. (Even though that's cheating at the game.)"

COOKIE_NAME = "rti_saves"       # The site's single cookie: holds what used to be saves.txt
COOKIE_PATH = "/"
COOKIE_MAX_AGE_DAYS = 400       # Browsers cap cookie lifetimes at 400 days; every save refreshes it
COOKIE_MAX_BYTES = 4000         # Browsers allow about 4 KB per cookie
AUTO_CLICK_MS = 1500            # Auto-click: presses the second-largest digit button this often
MUSIC_DEFAULT_VOLUME = 50       # Music player starting volume, 0-100

# =====================================================================
# 1. GAME DATA & CONFIGURATION
# =====================================================================

AUTOSAVE_MS = 30_000
NUMBER_PREFIX = "Last Significant Number: "
PLACES = 10  # Digit buttons: ones ... billions
CAP = 10 ** PLACES  # The biggest number the digit buttons can make
SILVER_COST = 10
MEDALS_PER_ROW = 10

def V(n, *arrows): return (arrows, n)

TRIDECAL = V(10, 10)  # 10^^^^^^^^^^10 - the end of the up-arrow stage
EXTRA_NAMES = [(TRIDECAL, "Tridecal")]  # Named numbers that have no medal of their own


class MedalDef(NamedTuple):
    medal_id: str
    at: tuple    # Bronze: value that unlocks it. Silver: value the game jumps to when bought.
    title: str
    desc: str
    name: str = ""  # Bronze: name shown for numbers at or above `at`
    text: str = ""  # Silver: milestone text
class AchievementDef(NamedTuple):
    target: tuple  # Collected when the value hits this exactly; missed once it's passed
    before_medal: str
    hint: str
    title: str
    desc: str
    number_name: str
    bg_label: str
    bg_file: str
class Theme(NamedTuple):
    bg: str
    fg: str
    frame: str
    font: str

INTRO_TEXT = "\n\n".join(["Hello, and welcome to Road Towards Infinity! This is a clicker game about exploring progressively bigger and bigger numbers...", "For now, you can only work with addition - but this is only the beginning! For now, click the button with the zero on it to start counting up to 10. Once you reach ten, the tens place will unlock, allowing you to add ten at a time. Digits will be unlocked like so until you reach ten billion - your first objective.", "Use the medals tab to track your progress. Use the settings screen to adjust choice of background, manage save states, or change the background theme.", "Themes can be unlocked via achievements, which are typically optional bonus challenges - can you puzzle out what the hints refer to, before it's too late?", "One more thing: The music player does not work too well with website links, and there's unfortunately not much I can do about that :/", "Anyways, good luck!",])
FIRST_MILESTONE_TEXT = "\n\n".join(["Hello again!", "If you are seeing this, that means you have reached ten billion - congratulations!", "How many of the bonus achievements did you snag? If you missed one, too bad, you'll just have to restart if you want it and/or want to 100% the game.", "You may have noticed that on the medals screen, you've been gaining something called Medal Points from when you collect Bronze Medals. You should now have ten - use them to purchase your very first Silver Medal, which will unlock the next stage of the game.", "But what is the next stage, you ask? Well, you may have noticed that it's gotten a bit tricky keeping track of the digits. To reach bigger numbers, we need more concise representations of those numbers.", "Enter exponents - now, the number is represented by a base (which will always be ten going forward) and something called an exponent. For now, think of the exponent as a count of how many digits the number has.", "Your next objective is to reach ten to the ten billion, also known as a trialogue.", "Be aware that you're going to get numbers far larger than you ever thought possible very quickly - good luck!",])
SECOND_MILESTONE_TEXT = "\n\n".join(["Hello, yet again!", "If you are seeing this, that means you have reached a trialogue - congratulations!", "Like before, if you missed an achievement and want it, you'll sadly just have to restart.", "You should have ten medal points again, go ahead and purchase your second silver medal to unlock the next stage.", "Speaking of the next stage...", "Once again, it's gotten a bit tricky keeping track of the digits. To reach even bigger numbers, we need more concise representations of those numbers - again.", "Now, last time, we were able to represent the digits by counting them in an exponent. Can we do the same here?", "Well, as it turns out, yes! This results in something called a power tower, and that's what the next stage is all about. It's going to be a longer stage ahead, fair warning.", "There's also something important to note here: Putting something inside another instance of the same thing - in this case, an exponent in an exponent - is known as RECURSION. Recursion is going to be very very important to understand, going forward.", "To represent this, every once in a while, there may be a new button available on the game screen labeled 'Recurse!'. Press it to induce recursion - which for now, just creates a new level of power tower.", "Your next objective is to reach a power tower of ten tens, also known as a decker.", "Good luck!",])
THIRD_MILESTONE_TEXT = "\n\n".join(["Hello, once again!", "Since you are seeing this message, you've officially reached a decker - congratulations, you are now well beyond most numbers people care about!", "If it seems like this took longer than usual, don't worry, that's actually just the first two milestoes being quicker to come than usual!", "As always, if you missed an achievement, you'd have to restart if you wanted to get it.", "As always, be sure to purchase the next silver medal with your medal points to unlock the next stage.", "Now, what's gone wrong is that it has become difficult to keep track of how tall the power tower is.", "To fix this, we need new notation...", "In 1976, Donald Knuth introduced something known as up-arrow notation. Basically, 10^10^10 = 10^^3, 10^^10^^10 = 10^^^3, etc - that's the best way I can explain it.", "Worth noting that we're going to start going through multuple levels of operation quickly here - so don't be surprised if things feel completely abstract going forward!", "At this point, the Recurse button will now be used to consolidate up-arrows. To unlock a brand-new arrow count, you need two instances of your current highest arrow count at the end of the number - 10^^^10^^^10 becomes 10^^^^3, but 10^^^10 alone won't do. Once an arrow count is unlocked, one instance is enough - so 10^^^10 can then become 10^^^^2.", "Consolidating is optional up to eight instances of the same arrow count at the end of the number. At nine, you must press it to consolidate the arrows.", "The new goal is to reach 10^^^^^^^^^^10, or a tridecal. Then, we will begin on array notation itself.", "Good luck!",])
FOURTH_MILESTONE_TEXT = "\n\n".join(["Hello, again again!", "Since you are reading this, that means you've finally reached a tridecal - congratulations, you have officially completed the earlygame!", "And yes, it was supposed to take a while to get up here.", "Of course, as always, if you missed an achievement, you'd have to restart if you wanted to get it.", "You know the drill at this point, silver medal, 10 points, yada-yada.", "What's next from here is to represent how many arrows are in a row as a number - simply by counting them.", "However, that leads to a third number so far.", "Hence, the introduction of array notation - which would be the next stage.", "However, I haven't implemented that yet - sorry!", "I'll announce when the next stage is actually built, don't worry.", "For now, uh, you won! yay!"])

BRONZE_MEDALS = [
    MedalDef("0A", V(10), "Multiple digits?!?", "Wow! How many digits can there be?", "Ten"),
    MedalDef("0B", V(100), "A Franklin", "CASH MONEYYY", "Hundred"),
    MedalDef("0C", V(10**3), "Thou art so numerous thou art like sand", "By medieval standards, this was a lot of people.", "Thousand"),
    MedalDef("0D", V(10**4), "Ben Franklin's Orchestra", "Ten grand can be called a band of Benjamins. Metal!", "Ten Thousand"),
    MedalDef("0E", V(10**5), "Edge of Space", "The Karman Line is a hundred thousand Minecraft Blocks\nabove sea level!", "Hundred Thousand"),
    MedalDef("0F", V(10**6), "Standard of Success", "If you have a million bucks, seriously, please retire - you don't\nneed more than that.", "Million"),
    MedalDef("0G", V(10**7), "Even More Innumerable", "Ten million is a lot of people by today's standards. That's like,\none whole world-class city!", "Ten Million"),
    MedalDef("0H", V(10**8), "Deep Space", "An astronomical unit - from the Earth to the Sun - is a little under 93 million miles...", "Hundred Million"),
    MedalDef("0I", V(10**9), "Typical Gov't Spending", "A stealth bomber costs about this much - a single high-tech plane!!", "Billion"),
    MedalDef("0J", V(10**10), "Having a Conversation", "I don't know why this is called a dialogue...", "Dialogue"),
    MedalDef("1A", V(100, 1), "The Center of the Infosphere", "Did you know that Google, the world's most used\nsearchengine was named Google because a graduate\nstudentmis-spelled a googol?", "Googol"),
    MedalDef("1B", V(500, 1), "Edge of Physics", "-ding is a modifier that multiples an exponent by five\n10^500 is estimated to be the size of the possibility space of String Theory.", "Googolding"),
    MedalDef("1C", V(10**3, 1), "Now comes as a bell for fish!", "-chime is a modifier that multiples an exponent by ten.\n-bell is a modifier that multiples an exponent by 50.\nSince a guppyis a number defined to be 10^20, that makes a\nguppybell 10^1000.", "Googolchime"),
    MedalDef("1D", V(10**4, 1), "Limit of Understanding", "-toll is a modifier that multiples an exponent by a hundred.\nA Googoltoll just so happens to be the largest\nnumber that Windows Calculator can handle!", "Googoltoll"),
    MedalDef("1E", V(10**5, 1), "Incomprehensible to Humans", "-gong is a modifier that multiples an exponent by a\nthousand. This number was invented by accident by a\nfriend of Sbiis Saibian when they tried to define the Googolplex.", "Googolgong"),
    MedalDef("1F", V(10**6, 1), "A Book Full of Zeros", "To write a million zeros would take a book 400 pages long\nwith 2500 zeroes on each page.", "Milliplexion"),
    MedalDef("1G", V(10**7, 1), "What's a Goospolplex?", "A goospol is ten million. -plex is a modifier that raises ten\nto the power of the number prior to the -plex suffix.\nSo a goospolplex is ten raised to the power of ten million.", "Goospolplex"),
    MedalDef("1H", V(10**8, 1), "Anyone want a smoke?", "-bong is a modifier that multiples an exponent by a million.\nConfusingly, this terminology has nothing to do with\na bong, which is a type of device used for herbal drugs like\ntobacco.", "Googolbong"),
    MedalDef("1I", V(10**9, 1), "A Library Full of Zeros", "To write this number would take a thousand volumes filled\nwith zeros as per the specification mentioned by\nMedal 1F.", "Billipexion"),
    MedalDef("1J", V(10**10, 1), "Three Way Conversation", "As per Medal 1G's definition of the -plex modifier, this\nnumber could be named a dialogueplex.", "Trialogue"),
    MedalDef("2A", V(100, 1, 1), "The Original Googolism", "Between 1920 and 1940, a googolplex was defined as\na '1 followed by writing zeros until you get tired.'\nIn 1940, it was formalized as one of the first ever googolisms as\n10^googol, or 10^10^100.", "Googolplex"),
    MedalDef("2B", V(10**6, 1, 1), "Start of Class 4 Numbers", "On the googology wiki, numbers are grouped by size.\nClass 4 is one of the smallest sizes, starting at a\nmillionduplex.", "Millionduplex"),
    MedalDef("2C", V(100, 1, 1, 1), "Operators: Deluxe Edition", "Do you need a shorter name for a googolplexplex?\nMaybe you think that -plex is an operator?\nLook no further, because today it is an operator! -plex is defined as\ntaking the number and using it as the exponent!", "Googolduplex"),
    MedalDef("2D", V(10**6, 1, 1, 1), "Start of Class 5 Numbers", "If a number has something between a base number\nname and the -plex operator, that means that\nthe plex operator is repeated a certain number of times.", "Millitriplexion"),
    MedalDef("2E", V(100, *[1] * 4), "Regarding Operator Counters", "For example, -du- indicates that the operator\napplies twice. So -duplex is the same as -plexplex.\nLikewise, -triplex is the same as -plexplexplex, since -tri- means\nthe operator is applied thrice.", "Googoltriplex"),
    MedalDef("2F", V(100, *[1] * 5), "Tetration Level", "The Googolquadriplex is the first number in the\nTetration Level classification on the wiki. Tetration is\nthe next step up from exponentiation, just as exponents are the\nnext step up from multiplication.", "Googolquadriplex"),
    MedalDef("2G", V(100, *[1] * 6), "Operator Counters, Continued", "-quadri- is an operator counter saying that\nthe operator applies four times. -quin- is an operator\ncounter that says the operator applies five times.", "Googolquinplex"),
    MedalDef("2H", V(100, *[1] * 7), "Dodging Birds and Bees...", "-hexa- is an operator counter saying that the\noperator applies six times. The alternative for this\nwas -[CENSORED]ti-, which is not being used for... reasons.", "Googolhexaplex"),
    MedalDef("2I", V(100, *[1] * 8), "The Origin of the Counters", "-hepta- or -septa- are operator counters saying\nthat the operator apples seven times. The\nsource for these counters is based off of Greek and Latin number\nmodifiers.", "Googolheptaplex"),
    MedalDef("2J", V(10, *[1] * 9), "The Power Skyscraper", "A decker is likely called that because it is a decuple-decker\n- as in, a power tower of tens ten (decuple-)\ntens tall.", "Decker"),
    MedalDef("3A", V(100, 2), "Launching into True Googology!", "A giggol is the next major googol-like number.\nIt is a power tower of tens a hundred tens\ntall, which is best reperesented as 10^^100.", "Giggol"),
    MedalDef("3B", V(10, 3), "Le Fancie K", "There's a number known as a Fancy K. It is\n10^^10^^10^^10^^10^^10^^10^^10^^10^^10,\naka 10^^^10. ...but why is called a fancy K???", "Fancy K"),
    MedalDef("3C", V(100, 3), "Regarding Names...", "A Gaggol is 10^^^100, or 10^^10^^10^^... ...^^10,\nwhere there's a hundred tens. Up here, names\nare very relevant for googology - a number almost doesn't exist in\ngoogology without a name!", "Gaggol"),
    MedalDef("3E", V(100, 4), "Taxi Time I!", "The -taxi series of number has to do with\narrow-notation numbers where the last number\nends in a power of ten.", "Geegol"),
    MedalDef("3F", V(100, 5), "Names, names, names...", "A geegol and a gigol are the next two googol\nlike numbers in Jonathan Bower's system, or the fourth\nand fifth numbers total, if the Googol itself is the first one.", "Gigol"),
    MedalDef("3G", V(100, 6), "Safety first!", "The sixth number in the series is the Goggol,\nnot to be confused with safety goggles.", "Goggol"),
    MedalDef("3H", V(100, 7), "The Funny Number", "The seventh number in the series is the Gagol.\nIt is also the last in this part of the series that Bowers named.", "Gagol"),
    MedalDef("3I", V(100, 8), "More Googol Series", "Bowers is not the only person to name numbers\nin a series that starts with the googol. Many do too -\nincluding Googology wiki user Arsygo.", "Gocgol"),
    MedalDef("3J", V(100, 9), "The Complete List", "The list Arsygo made is actually tacked on the\nend of Bowers' list. A gocgol is 10^^^^^^^^100, while\na gengol is 10^^^^^^^^^100.", "Gengol"),
    MedalDef("3K", V(10, 10), "Triple Decal Trouble!", "The Tridecal is 10^^^^^^^^^^10. For the sake\nof conciseness, this is the end of arrow notation...", "Tridecal")]
SILVER_MEDALS = [
    MedalDef("0Z", V(10, 1), "Next stop: Exponents", "Let's start counting how many digits we have!", text=FIRST_MILESTONE_TEXT),
    MedalDef("1Z", V(10, 1, 1), "Coming Up: Power Towers", "Now, it's time to nest exponents in one another!\nRecursion!", text=SECOND_MILESTONE_TEXT),
    MedalDef("2Z", V(10, 2), "Time to Start Counting Arrows", "Basic recursion of exponents has its limits. But\nwe need to go beyond - well beyond exponents..!", text=THIRD_MILESTONE_TEXT),
    MedalDef("3Z", TRIDECAL, "Arrays await! (Coming soon)", "This is only the beginning. Soon, there will be\nmore to come...", text=FOURTH_MILESTONE_TEXT),]
ACHIEVEMENTS = [
    AchievementDef(V(69), "0B", "( ͡° ͜ʖ ͡°)", "*Catcalls*", '"My, you are quite handsome!"', "Sixty-Nine", "NSFW Joke", "69"),
    AchievementDef(V(666), "0C", "What number do Christians most fear?", "The Mark of the Beast", "*Doom OST plays*", "Six Hundred and Sixty Six", "Demonic", "666"),
    AchievementDef(V(1337), "0D", "Ar3 y0u a l33t g@mer?", "L33t Xp3rt", "Welc0me t0 th3 b1g le@gues, pl@yer!", "One Thousand, Three Hundred, and Thirty-Seven", "L33t Sp33k", "hackorz"),
    AchievementDef(V(2763), "0D", "The Original Object Show's Favorite Number...", "CAKE AT STAKE!", "BFDI needs no introduction, considering how surprisingly big it is on the Internet even now...", "Two Thousand, Seven Hundred, and Sixty-Three", "Dream Island", "bfdi"),
    AchievementDef(V(12345), "0E", "Stupid Luggage Combination", "Spaceballs, the combo!", "If you had to pick a combination for a lock, pick literally anything else than this!", "Twelve Thousand, Three Hundred and Forty-Five", "Spaceballs", "spaceballs"),
    AchievementDef(V(262144), "0F", "The lever's long odds.", "I CAN'T STOP WINNING!", "A typical slot machine these days gives a one in 262,144 chance of winning.", "Two Hundred and Sixty Two Thousand and One Hundred and Fourty Four", "JACKPOT", "money"),
    AchievementDef(V(7500000), "0G", "How long did The Answer take?", "Deep Cut on Life and the Universe", "Everyone knows about 42, but did you know it took that computer 7.5 million years to calculate?", "Seven Million and Five Hundred Thousand", "Hitchhiker", "AttUQoLtUaE"),
    AchievementDef(V(92955807), "0H", "TO THE... sun?", "The Final Frontier", "These are the voyages...", "Ninety-Two Million, Nine Hundred and Fifty-Five Thousand, Eight Hundred and Seven", "The Infinite Dark", "cosmos"),
    AchievementDef(V(299792458), "0I", "The ultimate speed is...", "v = c", "Nothing goes faster than light. Except the fabric of reality itself :/", "Two Hundred and Ninety-Nine Million, Seven Hundred and Ninety-Two Thousand, Four Hundred and Fifty-Eight", "Massless Velocity", "light"),
    AchievementDef(V(8300678395), "0J", "Global Population Census", "The Total of Humanity", "Being Diverse Since the Stone Age!", "Eight Billion, Three Hundred Million, Six Hundred and Seventy-Eight Thousand, Three Hundred and Ninety-Five", "Human Variety", "diversity"),
    AchievementDef(V(81, 1), "1A", "How much Universe is there?", "The Grand Total of Existence", "There are six times ten to the eighty fundamental particles in the observable universe.", "One Sesvigintillion", "Universe", "particles"),
    AchievementDef(V(308, 1), "1B", "What's AD's most common limit?", "The Edge of Computability", "The largest a 64-bit floating point number can be is 2^1024, or 1.79*10^308. Beyond that limit, basic numerical compuations do not exist in most programming languages.", "One Hundred Uncentillion", "Compute Limit", "binary"),
    AchievementDef(V(12431, 1), "1E", "How creative did Nintendo let you be?", "MatPat's Retro Special", "The number of possible fun levels estimated to have been able to exist in Super Mario Maker was 10^12431. And no, Trimming the Herbs doesn't count!", "Marioplex", "[ERROR: NINTENDO]", "dmca"),
    AchievementDef(V(206545, 1), "1F", "Riddle of the Sun's Grazers", "Fun fact: Archimedes fantasized about ranching!", "In the mid-3rd century BCE, Archimedes wrote a 44 line poem asking a mathematical question involving cattle. It turns out that the answer, calculated over two thousand years later, was a grand total of 7.76*10^206544 cattle.", "Ten Octo-sexagintilli-septen-quadraginta-octingent-illion", "Ranching", "pasture"),
    AchievementDef(V(1834097, 1), "1G", "How Many Books Can Exist?", "The Library of Babel Does End!", "The Library of Babel is a thought experiment asking if a library could contain every possible book such that each book is 410 pages lone, with 40 lines per page, 80 characters per line, and  each of those characters being one of 25 possible characters in total.", "Hundred Un-deci-ses-centilli-quattuor-sexaginta-tre-cent-illion", "Finite Literature", "library"),
    AchievementDef(V(8924728, 1), "1G", "The Bard's Monkey Problem", "This is a classic example about the nature of infinity.", "The probability that a monkey randomly typing at a typewriter produces the complete works of William Shakespeare is 1 out of 48^5.3 million or so - equal to about 7.66*10^8924727", "Ten Billi-quattuor-septuaginta-nongentilli-octo-nongent-illion", "Monkey Business", "monkey"),
    AchievementDef(V(41024320, 1), "1H", "How far have we looked for indivisbility?", "The Largest Prime Ever", "The largest prime number ever found was just found in 2024! It is exactly (2^136279841) - 1.", "Ten Tre-decilli-quattuor-septuaginta-sescentilli-duo-septuaginta-septingent-illion", "PRIME!!!", "prime"),
    AchievementDef(V(1333333365, 1), "1J", "How long can a number name be?", "The Longest -illion 1", "-illion prefixes are a fast way to get a long name for a number if you know what you're doing!", "One Quattuor-quadraginta-quadrin-gentilli-quattuor-quadraginta-quadrin-gentilli-quattuor-quin-quaginta-quadrin-gent-illion", "Long Number 1", "long1"),
    AchievementDef(V(15, 1, 1), "2A", "How far can you go in the game that always has its next update 5 hours away?", "Limit of Hevipelle's Game", "10^10^15 is the upper limit of how much antimatter you can have in Hevipelle's hit game Antimatter Dimensions.", "One Maximusquadrillion", "Blurple Checkerboard", "antimatter"),
    AchievementDef(V(37, 1, 1), "2A", "Ancient Googology?? Starring the Buddha??", "The Buddha's Largest Number", "In Chapter 30 of the Avatamsaka Sutra, the Buddha teaches a king about large numbers. The maximum number listed is 10^(5*2^124), which is roughly 10^(1.33*10^37). ", "Hundred Quin-trigintilli-ses-quadraginta-quadringentilli-noven-septuagintilli-septem-octoginta-octingentilli-septe-nonaginta-quingentilli-ses-quin-quaginta-septingentilli-deci-ses-centilli-octo-sexaginta-septingentilli-octo-octoginta-centilli-quattuor-septuaginta-ducentilli-duo-quadraginta-centilli-duo-viginti-quingentilli-quin-vigin-tillion", "Buddhism", "buddha"),
    AchievementDef(V(102, 1, 1), "2B", "What is One Second of Eternity?", "SCP-7179: E is for Eternity", "In SCP-7179, a googol factorial years (roughly a little larger than a googolplex) was described as being one second of eternity.", "One Fzgoogol", "Secure. Contain. Protect.", "SCP"),
    AchievementDef(V(1997, 1, 1), "2B", "So much of a Goliath...", "The Devil in the Binary", "A Goliath number is a power of two such that the dgits include 666 instances of '666'.", "One Logolplex", "DemonBeeg", "bigDemon"),
    AchievementDef(V(3981, 1, 1), "2B", "Creeper? Aw man...", "So we back in the mines...", "10^10^215 is defined as the Minecraftplex - it is approximately the total number of possible ways blocks can be placed in a Minecraft world.", " One Googol-un-septuaginti-gong", "BEHIND YOU!", "creeper"),
    AchievementDef(V(4778815304, 1, 1), "2C", "TEMU version of Steam", "AI Slop Game Replica Central", "10^10^4,778,815,304 is definied as the Robloxplex - it is the estimated total number of games possible in the controversial game platform named Roblox.", "One Googol-plexi-chilia-tetra-gegi-gong", "Tallarico's Victim", "oof"),
    AchievementDef(V(34, 1, 1, 1), "2C", "Numberphile talked about this in 2015.", "Skewes the Nerd", "In 1933, using the Riemann Hypothesis, someone named Stanley Skewes found the upper bound for when the prime counting function would exceed the logarithmic integral - at 10^10^10^34.", "Ten to the Ten to the Ten to Thirty-Four.", "Riemann Party", "skewes"),
    AchievementDef(V(122, 1, 1, 1, 1, 1), "2G", "What is Reality's Wavelength?", "Poincare's Recurrence for the entire Universe", "A mathematician named Jon Page recently estimated the universe was at least 10^10^10^122 megaparsecs across. 10^10^10^10^10^122 would be the Poincare recurrence time of all the matter in a universe that size.", "Ten to the Ten to the Ten to the Ten to the Ten to One Hundred and Twenty Two.", "The Eternal Loop", "cycles"),
    AchievementDef(V(9999999999, 9, 9, 9, 9, 9, 9, 9, 9, 8, 8, 8, 8, 8, 8, 8, 8, 7, 7, 7, 7, 7, 7, 7, 7, 6, 6, 6, 6, 6, 6, 6, 6, 5, 5, 5, 5, 5, 5, 5, 5, 4, 4, 4, 4, 4, 4, 4, 4, 3, 3, 3, 3, 3, 3, 3, 3, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 1, 1, 1, 1, 1, 1), "3K", "MAXIMUM SPEARS! FUHUHU!!!", "The Deepest Corner", "This is the longest number that can occur in the number space for a long while. Savor it.", "'Undyne-kaxis'? (Name I made up)", "Rainbows of the True Hero's Corner", "corner"),
    #AchievementDef(V(), "", "", "", "", "", "", ""),
    ]
THEME_COLORS = {
    k: Theme(*v) for k, v in {
        "default": ("#d9d9d9", "black", "#f0f0f0", "Arial"),
        "69": ("#ffc0cb", "black", "#ffe4e1", "Comic Sans MS"),
        "666": ("#8b0000", "white", "#4a0000", "Impact"),
        "hackorz": ("#002b00", "#00ff00", "#001100", "Consolas"),
        "spaceballs": ("#2f4f4f", "white", "#1a2f2f", "Courier New"),
        "money": ("#006400", "gold", "#003300", "Georgia"),
        "AttUQoLtUaE": ("#4b0082", "white", "#2e0854", "Trebuchet MS"),
        "cosmos": ("#0b0b23", "#00ffff", "#050511", "Verdana"),
        "light": ("#ffffff", "#00008b", "#e0e0e0", "Arial"),
        "diversity": ("#ff8c00", "black", "#cc7000", "Tahoma"),
        "particles": ("#4682b4", "white", "#2d5986", "Arial"),
        "binary": ("#003300", "#33ff33", "#001a00", "Consolas"),
        "dmca": ("#cc0000", "white", "#800000", "Impact"),
        "pasture": ("#556b2f", "#ffffe0", "#38471f", "Georgia"),
        "library": ("#d2b48c", "#3e2723", "#b59a72", "Times New Roman"),
        "monkey": ("#8b4513", "#ffebcd", "#5c2c16", "Comic Sans MS"),
        "prime": ("#483d8b", "#e6e6fa", "#30285a", "Trebuchet MS"),
        "long1": ("#708090", "#ffffff", "#4f5d6a", "Verdana"),
        "antimatter": ("#87ceeb", "#000080", "#56b4d3", "Arial"),
        "buddha": ("#ffd700", "#8b0000", "#cca100", "Georgia"),
        "SCP": ("#363636", "#dcdcdc", "#222222", "Courier New"),
        "bigDemon": ("#191970", "#00ffff", "#0f0f47", "Impact"),
        "creeper": ("#006400", "#adff2f", "#003300", "Consolas"),
        "oof": ("#0000cd", "#ffffff", "#00008b", "Tahoma"),
        "skewes": ("#555555", "#ffffff", "#333333", "Arial"),
        "cycles": ("#2f4f4f", "#adff2f", "#1c3030", "Verdana"),
        "center": ("#7399d8", "#015bae", "#536fa9", "Arial"),
    }.items()}

FONT_FALLBACKS = {"Consolas": "'Courier New', monospace", "Courier New": "monospace", "Georgia": "'Times New Roman', serif", "Times New Roman": "serif",
                  "Comic Sans MS": "'Comic Neue', cursive", "Impact": "Haettenschweiler, 'Arial Narrow Bold', sans-serif"}
def css_font(name): return f'"{name}", {FONT_FALLBACKS.get(name, "Arial, Helvetica, sans-serif")}'

AUDIO_EXTENSIONS = (".mp3", ".ogg", ".oga", ".opus", ".wav", ".m4a", ".aac", ".flac", ".weba", ".webm", ".mp4")

# =====================================================================
# 2. PAGE STYLE & LAYOUT
# =====================================================================

CSS = r"""
:root {
  --bg: #d9d9d9; --fg: black; --frame: #f0f0f0; --font: Arial, Helvetica, sans-serif;
  --bg-image: none; --shader-image: none;
  --top-h: 20vh;                                       /* Number display: 20% of the window, like the original */
  --spacer-w: min(calc(var(--top-h) * 1.5), 30vw);     /* Centre image, capped so narrow screens keep room for text */
}
@supports (height: 1dvh) { :root { --top-h: 20dvh; } }
* { box-sizing: border-box; }
html, body { margin: 0; height: 100%; overflow: hidden; }
body { background: var(--bg); color: var(--fg); font: 10pt var(--font); }
#app { display: flex; flex-direction: column; height: 100%; }
[hidden] { display: none !important; }

button, select, input { font: inherit; font-family: var(--font); color: var(--fg); background: var(--frame); }
button { border: 2px outset var(--frame); padding: 3px 10px; cursor: pointer; white-space: pre-line; }
button:active:not(:disabled), button.pressed:not(:disabled), button.selected { background: var(--fg); color: var(--frame); border-style: inset; }
button:disabled { color: color-mix(in srgb, var(--fg) 40%, var(--frame)); cursor: default; }
button:focus-visible { outline: 2px dotted var(--fg); outline-offset: -5px; }
input[type=text], input[type=url], select { border: 2px inset var(--frame); padding: 3px 5px; min-width: 0; }

#screens { flex: 1; min-height: 0; position: relative; }
.screen { position: absolute; inset: 0; display: none; flex-direction: column; }
.screen.active { display: flex; }
/* The tiled background stays put while the content scrolls over it */
.canvas { position: relative; flex: 1; min-height: 0; isolation: isolate; background-color: var(--bg); }
.canvas::before, .canvas::after { content: ""; position: absolute; inset: 0; pointer-events: none; background-repeat: repeat; background-position: 0 0; }
.canvas::before { background-image: var(--bg-image); z-index: 0; }
/* Shader: darkens the background by up to 35%, the same maths as the original's image processing */
.canvas::after { background-image: var(--shader-image); filter: grayscale(1) brightness(1.7); opacity: 0.35; mix-blend-mode: multiply; z-index: 1; }
body.shader-off .canvas::after { display: none; }
.scroll { position: absolute; inset: 0; overflow: auto; z-index: 2; scrollbar-color: var(--frame) var(--bg); }

/* Game screen */
#stats { flex: none; display: grid; grid-template-columns: minmax(0, 1fr) auto minmax(0, 1fr); height: calc(var(--top-h) + 4px); background: var(--frame); }
.fit { display: flex; align-items: center; justify-content: center; text-align: center; overflow: hidden; padding: 0 7px; font-weight: bold;
       line-height: 1.15; overflow-wrap: anywhere; background: var(--frame); color: var(--fg); }
.spacer { width: var(--spacer-w); display: flex; justify-content: center; }
.spacer-frame { display: flex; align-items: center; height: 100%; border: 2px outset var(--frame); }
#spacer-img { display: block; max-width: calc(var(--spacer-w) - 4px); max-height: var(--top-h); }
.measurer { position: absolute; left: -10000px; top: 0; visibility: hidden; font-weight: bold; line-height: 1.15; overflow-wrap: anywhere; white-space: normal; text-align: center; }
#game-toolbar { padding: 20px 20px 0; }
#game-toolbar.locked { visibility: hidden; }
#auto-btn { font-size: 12pt; font-weight: bold; }
#buttons-frame { display: inline-flex; flex-wrap: wrap; align-items: flex-start; row-gap: 10px; max-width: calc(100% - 40px);
                 margin: 10px 20px 20px; padding: 10px 0 10px 10px; background: var(--frame); }
#buttons-frame:empty { display: none; }
#buttons-frame > * { margin-right: 10px; }
#buttons-frame > .flush { margin-right: 0; }
.digit { font-size: 30pt; font-weight: bold; min-width: 1.4em; padding: 0 12px; }
.exp-label { font-size: 30pt; font-weight: bold; color: var(--fg); background: var(--frame); white-space: nowrap; line-height: 1.3; }
#recurse-btn { font-size: 20pt; font-weight: bold; border-width: 5px; }

/* Settings screen */
#settings-layout { display: grid; grid-template-columns: auto minmax(0, 1fr) auto; align-items: start; }
#left-col { justify-self: start; display: flex; flex-direction: column; gap: 10px; }
.panel { display: flex; flex-direction: column; background: var(--frame); }
.panel > button, .panel > .panel-label { width: 100%; }
.panel-label { text-align: center; padding: 3px 6px; }
#saves-panel { justify-self: center; min-width: 260px; }
#bgs-panel { justify-self: end; }
#bgs-grid { display: grid; grid-template-columns: auto auto; }
#bgs-grid button { margin: 2px; }
.save-row { display: flex; margin: 5px 0; }
.save-row > * { flex: 1 1 0; }
.save-row .save-preview { flex: 0 0 auto; display: flex; align-items: center; justify-content: center; text-align: center; white-space: pre; padding: 2px 8px; }
.save-row button { font-size: 14pt; }
#cookie-warning { padding: 6px; max-width: 260px; text-align: center; font-weight: bold; }
#music-panel { width: 280px; padding-bottom: 4px; }
#music-panel > * { margin: 2px 4px; }
.music-row { display: flex; gap: 4px; }
.music-row > * { flex: 1 1 0; }
#music-url { flex: 1 1 auto; }
#music-load { flex: 0 0 auto; }
#music-volume { accent-color: var(--fg); }
#music-status { text-align: center; font-style: italic; overflow-wrap: anywhere; min-height: 1.3em; }
@media (max-width: 720px) {
  #settings-layout { grid-template-columns: minmax(0, 1fr); row-gap: 12px; }
  #left-col, #saves-panel, #bgs-panel, #music-panel { justify-self: stretch; min-width: 0; width: auto; }
}

/* Achievements & Medals */
.stat-label { font-size: 12pt; font-weight: bold; text-align: center; padding: 4px; background: var(--frame); border: 2px outset var(--frame); }
#ach-grid { display: flex; flex-wrap: wrap; gap: 10px; padding: 15px; }
#medal-stats { display: flex; }
#medal-stats > * { flex: 1 1 0; }
#medal-grid { display: inline-grid; grid-template-columns: repeat(13, auto); align-items: center; gap: 10px; padding: 15px; background: var(--frame); }
.row-label { font-size: 24pt; color: var(--fg); justify-self: start; white-space: nowrap; }
.collectible { width: 60px; height: 60px; flex: none; border: 5px outset var(--frame); background: var(--frame); color: var(--fg);
               font: 24pt Tahoma, Verdana, sans-serif; line-height: 50px; text-align: center; user-select: none; -webkit-user-select: none; }
.collectible.clickable { cursor: pointer; }
#tooltip { position: fixed; z-index: 200; max-width: min(480px, 92vw); padding: 1px 3px; white-space: pre-wrap; font: 8pt Tahoma, Verdana, sans-serif;
           background: var(--frame); color: var(--fg); border: 1px solid var(--fg); pointer-events: none; }

/* Bottom menu */
#menus { flex: none; display: flex; background: var(--frame); }
#menus > button { flex: 1 1 0; padding: 6px 4px; }
#quit-btn { color: red; }

/* Pop-ups */
.modal-overlay { position: fixed; inset: 0; z-index: 100; display: flex; align-items: center; justify-content: center; background: rgba(0, 0, 0, 0.45); }
.modal { display: flex; flex-direction: column; max-width: 50vw; min-width: 260px; max-height: 88vh; background: var(--frame); color: var(--fg);
         border: 2px outset var(--frame); box-shadow: 0 6px 24px rgba(0, 0, 0, 0.35); }
.modal-title { padding: 6px 10px; font-weight: bold; background: var(--fg); color: var(--frame); }
.modal-title:empty { display: none; }
.modal-body { padding: 20px; overflow: auto; white-space: pre-wrap; text-align: left; }
.cookie-body { white-space: normal; }
.modal-ok { align-self: center; min-width: 10ch; margin: 0 0 10px; }
@media (max-width: 720px) { .modal { max-width: 92vw; } }
"""

PAGE_HTML = """
<main id="screens">
  <section class="screen" id="screen-game">
    <div id="stats">
      <div class="fit" id="num-name"></div>
      <div class="spacer"><span class="spacer-frame"><img id="spacer-img" alt=""></span></div>
      <div class="fit" id="num-number"></div>
    </div>
    <div class="canvas"><div class="scroll">
      <div id="game-toolbar" class="locked"><button type="button" id="auto-btn" title="Presses the second-largest digit button every 1.5 seconds">Auto-Click: On</button></div>
      <div id="buttons-frame"></div>
    </div></div>
  </section>
  <section class="screen" id="screen-settings">
    <div class="canvas"><div class="scroll"><div id="settings-layout">
      <div id="left-col">
        <div class="panel" id="shader-panel">
          <div class="panel-label">Background Shader</div>
          <button type="button" id="shader-btn">Shader: On</button>
        </div>
        <div class="panel" id="music-panel">
          <div class="panel-label">Music Player</div>
          <div class="music-row">
            <input type="url" id="music-url" placeholder="Paste a link to audio or a page with audio" spellcheck="false">
            <button type="button" id="music-load">Play Link</button>
          </div>
          <select id="music-tracks" hidden></select>
          <div class="music-row">
            <button type="button" id="music-toggle" disabled>Pause</button>
            <button type="button" id="music-stop" disabled>Stop</button>
            <button type="button" id="music-loop">Loop: Off</button>
          </div>
          <label class="music-row" style="align-items:center">Volume <input type="range" id="music-volume" min="0" max="100"></label>
          <div id="music-status"></div>
        </div>
      </div>
      <div class="panel" id="saves-panel">
        <div class="panel-label">Manage save states here!</div>
        <button type="button" id="create-save-btn">Create New Save File</button>
        <div id="cookie-warning" hidden>Your browser is blocking this site's cookie, so saves will be lost when you leave the page.</div>
        <div id="save-rows"></div>
      </div>
      <div class="panel" id="bgs-panel">
        <div class="panel-label">Unlocked Backgrounds</div>
        <button type="button" id="default-bg-btn">Default</button>
        <div id="bgs-grid"></div>
      </div>
    </div></div></div>
  </section>
  <section class="screen" id="screen-ach">
    <div class="canvas"><div class="scroll">
      <div class="stat-label" id="ach-stats"></div>
      <div id="ach-grid"></div>
    </div></div>
  </section>
  <section class="screen" id="screen-medals">
    <div class="canvas"><div class="scroll">
      <div id="medal-stats"><div class="stat-label" id="bronze-stat"></div><div class="stat-label" id="silver-stat"></div><div class="stat-label" id="points-stat"></div></div>
      <div id="medal-grid"></div>
    </div></div>
  </section>
</main>
<nav id="menus">
  <button type="button" data-screen="settings">Settings</button>
  <button type="button" data-screen="game" class="needs-save" disabled>Game</button>
  <button type="button" id="quit-btn">Quit Game</button>
  <button type="button" data-screen="ach" class="needs-save" disabled>Achievements</button>
  <button type="button" data-screen="medals" class="needs-save" disabled id="medals-btn">Medals</button>
</nav>
<div id="tooltip" hidden></div>
<div id="cookie-notice" class="modal-overlay" hidden>
  <div class="modal" role="dialog" aria-modal="true">
    <div class="modal-title" id="cookie-notice-title"></div>
    <div class="modal-body cookie-body" id="cookie-notice-text"></div>
    <button class="modal-ok" type="button" id="cookie-notice-ok">OK</button>
  </div>
</div>
<div id="msg-box" class="modal-overlay" hidden>
  <div class="modal" role="dialog" aria-modal="true">
    <div class="modal-title" id="msg-box-title"></div>
    <div class="modal-body" id="msg-box-text"></div>
    <button class="modal-ok" type="button" id="msg-box-ok">OK</button>
  </div>
</div>
"""

# =====================================================================
# 3. STATE MANAGEMENT
# =====================================================================

class GameState:
    def __init__(self):
        self.current_save, self.autosave_job, self.loading = -1, None, False
        self.reset()
    def reset(self):
        self.arrows, self.n = [], 0
        self.ach = self.bronze = self.silver = self.points = self.to_collect = 0
    @property
    def value(self): return V(self.n, *self.arrows)
    @value.setter
    def value(self, v): self.arrows, self.n = list(v[0]), v[1]

state = GameState()
savestates = []
view = SimpleNamespace(background="default", font_family="Arial", screen=None, exponent_labels=[], exponent_texts=[], frame_keys=[], shader_on=True, auto_on=True)

# =====================================================================
# 4. PAGE SETUP & DOM HELPERS
# =====================================================================

_style = document.createElement("style")
_style.textContent = CSS
document.head.appendChild(_style)
_app = document.createElement("div")
_app.id = "app"
_app.innerHTML = PAGE_HTML
document.body.appendChild(_app)
_icon = document.createElement("link")
_icon.rel, _icon.href = "icon", ASSET_BASE + "icon.png"
document.head.appendChild(_icon)

_proxies = []  # Keeps event-handler proxies alive for the life of the page
def on(target, event, handler):
    proxy = create_proxy(handler)
    _proxies.append(proxy)
    target.addEventListener(event, proxy)
def by_id(element_id): return document.getElementById(element_id)
def el(tag, cls="", text=None, **attrs):
    node = document.createElement(tag)
    if cls: node.className = cls
    if text is not None: node.textContent = text
    for key, value in attrs.items(): node.setAttribute(key.replace("_", "-"), str(value))
    return node
def set_css(name, value): document.documentElement.style.setProperty(name, value)
def progress_text(label, count, total): return f"{label}: {count}/{total} ({100 * count / total:.2f}%)"

SCREENS = {name: by_id(f"screen-{name}") for name in ("game", "settings", "ach", "medals")}
buttons_frame = by_id("buttons-frame")
recurse_button = el("button", text="Recurse!", id="recurse-btn", type="button")
auto_button, game_toolbar = by_id("auto-btn"), by_id("game-toolbar")
digit_buttons = [None] * PLACES
ach_stats, bronze_stat, silver_stat, points_stat = (by_id(i) for i in ("ach-stats", "bronze-stat", "silver-stat", "points-stat"))
medals_btn, tooltip = by_id("medals-btn"), by_id("tooltip")
set_css("--shader-image", f'url("{ASSET_BASE}backgrounds/shader.png")')
spacer_img = by_id("spacer-img")
on(spacer_img, "error", lambda e: setattr(spacer_img, "hidden", True))
spacer_img.src = ASSET_BASE + "spacer.png"

# =====================================================================
# 5. DISPLAY & LAYOUT HELPERS
# =====================================================================

class FitLabel:
    """A label whose font shrinks or grows so its text always fills its box."""
    def __init__(self, element, raw):
        self.el, self.raw = element, raw

num_name = FitLabel(by_id("num-name"), NUMBER_PREFIX + "Zero")
num_number = FitLabel(by_id("num-number"), "0")
_fit_cache = {}
measurer = el("div", "measurer")
document.body.appendChild(measurer)
TOKEN_RE = re.compile(r"10|\^+|[a-zA-Z0-9]+|[^\w\s]|.")

def wrap_points(text):  # Invisible break points between "10", "^^^" and other tokens, so long numbers wrap at sensible places
    return "\n".join(" ".join("​".join(TOKEN_RE.findall(word)) for word in para.split()) for para in text.split("\n"))
def fits(text, wrap_w, max_h, size):
    measurer.style.fontSize = f"{size}px"
    measurer.textContent = text
    return measurer.scrollHeight <= max_h and measurer.scrollWidth <= wrap_w
def autowrap(label):
    wrap_w, max_h = int(label.el.clientWidth - 15), int(label.el.clientHeight - 4)
    if wrap_w <= 0 or max_h <= 0: return
    text = wrap_points(label.raw)
    key = (re.sub(r"\d", "0", label.raw), wrap_w, max_h, view.font_family)
    if key not in _fit_cache:
        measurer.style.width = f"{wrap_w}px"
        measurer.style.fontFamily = css_font(view.font_family)
        lo, hi = 4, max(12, int(max_h * 0.5))
        if fits(text, wrap_w, max_h - 6, lo):
            while lo < hi:
                mid = (lo + hi + 1) // 2
                lo, hi = (mid, hi) if fits(text, wrap_w, max_h - 6, mid) else (lo, mid - 1)
        _fit_cache[key] = lo
    label.el.textContent = text
    label.el.style.fontSize = f"{_fit_cache[key]}px"
def set_label(label, text):
    label.raw = text
    autowrap(label)
def refit_numbers(*_):
    autowrap(num_name)
    autowrap(num_number)
# Re-fit the number display whenever the browser window (and so the display) changes size
_resize_proxy = create_proxy(refit_numbers)
js.ResizeObserver.new(_resize_proxy).observe(by_id("stats"))

def tile_background():
    # The default background sits underneath, so it shows if this theme has no image of its own
    set_css("--bg-image", f'url("{ASSET_BASE}backgrounds/{view.background}.png"), url("{ASSET_BASE}backgrounds/default.png")')
def refresh_highlights():
    for name, button in theme_buttons.items(): button.classList.toggle("selected", name == view.background)
    shader_button.textContent = f"Shader: {'On' if view.shader_on else 'Off'}"
    shader_button.classList.toggle("selected", view.shader_on)
    auto_button.textContent = f"Auto-Click: {'On' if view.auto_on else 'Off'}"
    auto_button.classList.toggle("selected", view.auto_on)
def toggle_shader():
    view.shader_on = not view.shader_on
    document.body.classList.toggle("shader-off", not view.shader_on)
    refresh_highlights()
def update_bg(name):
    view.background = name
    c = THEME_COLORS.get(view.background, THEME_COLORS["default"])
    view.font_family = c.font
    for var, value in (("--bg", c.bg), ("--fg", c.fg), ("--frame", c.frame), ("--font", css_font(c.font))): set_css(var, value)
    refresh_highlights()
    tile_background()
    refit_numbers()
def layout_game_widgets():
    keys = [("label", i) for i in range(len(view.exponent_labels))] + [("digit", p) for p in reversed(range(PLACES)) if digit_buttons[p] is not None]
    if recurse_action(): keys.append(("recurse", 0))
    if keys == view.frame_keys: return
    view.frame_keys = keys
    widgets = [view.exponent_labels[i] if kind == "label" else digit_buttons[i] if kind == "digit" else recurse_button for kind, i in keys]
    for index, (kind, _) in enumerate(keys):  # Exponent labels sit flush: 10^^10^^10^^
        widgets[index].classList.toggle("flush", kind == "label" and index + 1 < len(keys) and keys[index + 1][0] == "label")
    buttons_frame.replaceChildren(*widgets)
def show_screen(name):
    for key, screen in SCREENS.items(): screen.classList.toggle("active", key == name)
    view.screen = name
    hide_tip()
    if name == "game": refit_numbers()

# Pop-up message boxes, shown one at a time
_msg_queue = []
_msg = SimpleNamespace(open=False)
def custom_msg_box(title, text):
    _msg_queue.append((title, text))
    if not _msg.open: show_next_msg()
def show_next_msg(*_):
    if not _msg_queue:
        _msg.open = False
        by_id("msg-box").hidden = True
        return
    title, text = _msg_queue.pop(0)
    _msg.open = True
    by_id("msg-box-title").textContent = title
    by_id("msg-box-text").textContent = text
    by_id("msg-box-text").scrollTop = 0
    by_id("msg-box").hidden = False
    by_id("msg-box-ok").focus()
on(by_id("msg-box-ok"), "click", show_next_msg)
def modal_open(): return _msg.open or not by_id("cookie-notice").hidden

# =====================================================================
# 6. COLLECTIBLES COMPONENT
# =====================================================================

_tip = SimpleNamespace(owner=None)
def show_tip(owner):
    if not owner.hover_text: return
    _tip.owner = owner
    tooltip.textContent = owner.hover_text
    tooltip.hidden = False
    r = owner.el.getBoundingClientRect()
    x = min(r.left + 20, window.innerWidth - tooltip.offsetWidth - 4)
    y = r.bottom + 5
    if y + tooltip.offsetHeight > window.innerHeight - 4: y = max(4, r.top - tooltip.offsetHeight - 5)
    tooltip.style.left, tooltip.style.top = f"{max(4, x)}px", f"{y}px"
def hide_tip(owner=None):
    if owner is not None and owner is not _tip.owner: return
    _tip.owner = None
    tooltip.hidden = True

class Collectible:
    ICONS = {"ach": "🏅", "bronze": "🥉", "silver": "🥈"}
    def __init__(self, parent, kind, key, hint, text, at):
        self.kind, self.key, self.hint, self.text, self.at = kind, key, hint, text, at
        self.clickable = kind != "ach"
        self.tip_job = None
        self.el = el("div", "collectible clickable" if self.clickable else "collectible")
        parent.appendChild(self.el)
        self.reset()
        if self.clickable: on(self.el, "click", self.on_click)
        on(self.el, "mouseenter", lambda e: show_tip(self))
        on(self.el, "mouseleave", lambda e: hide_tip(self))
        on(self.el, "pointerdown", self.on_touch)
    def on_touch(self, event):  # Touch screens have no hover, so a tap shows the tip for a few seconds
        if event.pointerType != "touch": return
        show_tip(self)
        if self.tip_job is not None: clear_timeout(self.tip_job)
        self.tip_job = set_timeout(lambda: hide_tip(self), 3500)
    def set_icon(self, icon): self.el.textContent = icon
    def reset(self):
        self.is_collected, self.enabled, self.hover_text = False, not self.clickable, self.hint
        self.set_icon("❓" if self.enabled else "🔒")
    def set_enabled(self, status=True):
        if self.clickable and status and not self.enabled:
            state.to_collect += 1
            refresh_stats()
        if self.kind == "silver" and status: self.milestone_btn.disabled = False
        self.enabled = status
        if not self.is_collected: self.set_icon("❓" if status else "❌")
    def collect(self):
        if not self.enabled or self.is_collected: return False
        self.is_collected, self.hover_text = True, self.text
        self.set_icon(self.ICONS[self.kind])
        if _tip.owner is self: tooltip.textContent = self.text
        if self.kind == "ach":
            state.ach += 1
            bg_buttons[self.key - 1].hidden = False
        else:
            state.to_collect -= 1
            if self.kind == "bronze": state.bronze, state.points = state.bronze + 1, state.points + 1
            else:
                state.silver, state.points, state.value = state.silver + 1, 0, self.at
                reset_digit_buttons()
        refresh_stats()
        return True
    def on_click(self, event=None):
        if self.collect(): update_main()
        check_silver_unlock()

# =====================================================================
# 7. UI SCREENS CONSTRUCTION
# =====================================================================

medal_grid = by_id("medal-grid")
medal_widgets, bronze_widgets, silver_widgets = [], [], []

def add_medal(kind, m):
    hint = f"Costs {SILVER_COST} Medal Points." if kind == "silver" else "???"
    widget = Collectible(medal_grid, kind, m.medal_id, f"Medal {m.medal_id}\nDesc: {hint}", f"{m.title}\nDesc: {m.desc}", m.at)
    medal_widgets.append(widget)
    return widget

for row in range((len(BRONZE_MEDALS) + MEDALS_PER_ROW - 1) // MEDALS_PER_ROW):
    medal_grid.appendChild(el("div", "row-label", f"Row {row}:"))
    bronze_row = BRONZE_MEDALS[row * MEDALS_PER_ROW:(row + 1) * MEDALS_PER_ROW]
    for m in bronze_row: bronze_widgets.append(add_medal("bronze", m))
    if row < len(SILVER_MEDALS):  # A row's silver medal is optional
        silver = add_medal("silver", SILVER_MEDALS[row])
        silver.milestone_text = SILVER_MEDALS[row].text or f"MILESTONE {row} ACHIEVED"
        silver.milestone_btn = el("button", text="See Row Completion\nMilestone Text", type="button")
        silver.milestone_btn.disabled = True
        on(silver.milestone_btn, "click", lambda e, t=silver.milestone_text: custom_msg_box("MILESTONE ACHIEVED", t))
        medal_grid.appendChild(silver.milestone_btn)
        silver_widgets.append(silver)

MEDAL_KEYS = [m.key for m in medal_widgets]
shader_button = by_id("shader-btn")
on(shader_button, "click", lambda e: toggle_shader())
default_bg_button = by_id("default-bg-btn")
on(default_bg_button, "click", lambda e: update_bg("default"))
bg_buttons = []
for index, a in enumerate(ACHIEVEMENTS):
    button = el("button", text=a.bg_label, type="button")
    button.hidden = True
    button.style.gridRow, button.style.gridColumn = str(index // 2 + 1), str(index % 2 + 1)
    on(button, "click", lambda e, f=a.bg_file: update_bg(f))
    by_id("bgs-grid").appendChild(button)
    bg_buttons.append(button)
theme_buttons = {"default": default_bg_button, **{a.bg_file: button for a, button in zip(ACHIEVEMENTS, bg_buttons)}}
on(by_id("create-save-btn"), "click", lambda e: create_save())
save_rows = by_id("save-rows")

def on_save_rows_click(event):  # One listener for every save row's buttons
    button = event.target.closest("button")
    if not button or button.disabled: return  # A JS null arrives as pyodide's jsnull, which is falsy (not None)
    index = int(button.getAttribute("data-index"))
    if button.getAttribute("data-action") == "load": load_save(index)
    else: delete_save(index)
on(save_rows, "click", on_save_rows_click)

ach_grid = by_id("ach-grid")
achievement_widgets = [Collectible(ach_grid, "ach", number, f"Name: ???\nCollect before Medal {a.before_medal}.\nHint: {a.hint}", f"{a.title}\nDesc: {a.desc}", a.target)
                       for number, a in enumerate(ACHIEVEMENTS, start=1)]

for button in document.querySelectorAll("#menus [data-screen]"):
    on(button, "click", lambda e, s=button.getAttribute("data-screen"): show_screen(s))
on(by_id("quit-btn"), "click", lambda e: quit_game())
LOCKED_UNTIL_SAVE_LOADED = list(document.querySelectorAll("#menus .needs-save"))

def on_buttons_frame_click(event):  # Digit buttons and the Recurse button
    button = event.target.closest("button")
    if not button or button.disabled: return
    place = button.getAttribute("data-place")
    if place: add_to_value(10 ** int(place))
    elif button.id == "recurse-btn": recurse()
on(buttons_frame, "click", on_buttons_frame_click)
def toggle_auto():
    view.auto_on = not view.auto_on
    refresh_highlights()
on(auto_button, "click", lambda e: toggle_auto())

# =====================================================================
# 8. GAME LOGIC & EVENT HANDLERS
# =====================================================================

def refresh_stats():
    ach_stats.textContent = progress_text("Achievements Collected", state.ach, len(ACHIEVEMENTS))
    bronze_stat.textContent = progress_text("Bronze Medals Collected", state.bronze, len(BRONZE_MEDALS))
    silver_stat.textContent = progress_text("Silver Medals Collected", state.silver, len(SILVER_MEDALS))
    points_stat.textContent = f"Medal Points: {state.points}"
    medals_btn.textContent = "Medals" if state.to_collect == 0 else f"Medals ({state.to_collect})"
def check_silver_unlock():
    widget = next((w for w in silver_widgets if not w.is_collected), None)
    if widget and not widget.enabled and state.points >= SILVER_COST:
        widget.set_enabled()
        if not state.loading: custom_msg_box("MILESTONE ACHIEVED", widget.milestone_text)
def reset_digit_buttons():
    for btn in digit_buttons:
        if btn is not None: btn.remove()
    digit_buttons[:] = [None] * PLACES
    view.frame_keys = []
def add_to_value(amount):
    state.n += amount
    update_main()
def trailing_run():
    a = state.arrows
    return next((i for i, x in enumerate(reversed(a)) if x != a[-1]), len(a)) if a else 0
def recurse_action():
    if state.silver == 2 and state.n >= CAP: return "append"  # Power towers: add a level
    if state.silver == 3 and state.arrows and state.value < TRIDECAL:  # Up-arrows
        merge_threshold = 2 if state.arrows[-1] + 1 > max(state.arrows) else 1
        if state.n == 10 and trailing_run() >= merge_threshold: return "merge"
        if state.n >= CAP or (state.n >= 100 and str(state.n).rstrip("0") == "1"): return "append"
    return None
def recurse():
    action = recurse_action()
    if action == "merge":  # 10^^10^^10 -> 10^^^3, 10^^10 -> 10^^^2: k matching arrows followed by 10 become one more arrow, then k + 1
        run = trailing_run()
        state.value = V(run + 1, *state.arrows[:-run], state.arrows[-1] + 1)
    elif action == "append": state.value = V(len(str(state.n)) - 1, *state.arrows, 1)
    reset_digit_buttons()
    update_main()
def digits_frozen():
    return state.value >= TRIDECAL or state.n >= CAP or (recurse_action() == "merge" and trailing_run() >= 9)  # Nine matching arrows must be merged
def update_main():
    state.n = min(state.n, CAP)
    texts = [f"10{'^' * a}" for a in state.arrows]
    if view.exponent_texts != texts:
        for label in view.exponent_labels: label.remove()
        view.exponent_labels, view.exponent_texts, view.frame_keys = [el("span", "exp-label", t) for t in texts], texts, []
    if state.value < TRIDECAL:
        for place in range(PLACES):
            if (place == 0 or state.n >= 10 ** place) and digit_buttons[place] is None:
                digit_buttons[place] = el("button", "digit", type="button", data_place=place)
    frozen = digits_frozen()
    for place, btn in enumerate(digit_buttons):
        if btn is not None:
            btn.textContent = "10" if place == PLACES - 1 and state.n >= CAP else str(state.n // 10 ** place % 10)
            btn.disabled = frozen
    layout_game_widgets()  # Also shows/hides the Recurse button
    for widget in bronze_widgets:
        if not widget.enabled and state.value >= widget.at: widget.set_enabled()
    for widget in achievement_widgets:
        if widget.enabled and not widget.is_collected:
            if state.value == widget.at: widget.collect()
            elif state.value > widget.at: widget.set_enabled(False)  # Passed it: missed for good
    named = [(at, name) for at, name in EXTRA_NAMES if state.value >= at] + [(m.at, m.name) for m in BRONZE_MEDALS if state.value >= m.at]
    named += [(a.target, a.number_name) for w, a in zip(achievement_widgets, ACHIEVEMENTS) if w.is_collected and state.value >= a.target]
    set_label(num_name, NUMBER_PREFIX + (max(named, key=lambda x: x[0])[1] if named else "Zero"))
    set_label(num_number, "".join(f"10{'^' * a}" for a in state.arrows) + str(state.n))
    game_toolbar.classList.toggle("locked", not auto_unlocked())

# ---------- Auto-click: slow automation, unlocked once the tens place is reached ----------
def auto_unlocked(): return state.current_save >= 0 and bronze_widgets[0].enabled  # Medal 0A unlocks when the number first reaches 10
def auto_click():
    if not view.auto_on or not auto_unlocked() or modal_open(): return
    places = [p for p, b in enumerate(digit_buttons) if b is not None]
    if len(places) < 2: return  # Needs a second-largest digit button on screen
    btn = digit_buttons[places[-2]]
    if btn.disabled: return
    btn.classList.add("pressed")
    set_timeout(lambda: btn.classList.remove("pressed"), 150)
    add_to_value(10 ** places[-2])
set_interval(auto_click, AUTO_CLICK_MS)

# =====================================================================
# 9. SAVE / LOAD UTILITIES (the save "file" is the site's one cookie)
# =====================================================================

def saves_text(lines): return "".join(line + "\n" for line in lines)
def encode_saves(lines): return js.encodeURIComponent(saves_text(lines))
def read_cookie_text():
    prefix = COOKIE_NAME + "="
    for part in str(document.cookie).split(";"):
        part = part.strip()
        if part.startswith(prefix):
            try: return js.decodeURIComponent(part[len(prefix):])
            except Exception: return None
    return None
def read_saves():
    text = read_cookie_text()
    return [line.strip() for line in text.splitlines() if line.strip()] if text else []
def write_saves():
    encoded = encode_saves(savestates)
    if len(encoded) > COOKIE_MAX_BYTES:
        custom_msg_box("SAVE ERROR", "There isn't enough room left in the save cookie. Delete a save file to make room.")
        return
    secure = "; Secure" if window.location.protocol == "https:" else ""
    document.cookie = f"{COOKIE_NAME}={encoded}; Max-Age={COOKIE_MAX_AGE_DAYS * 86400}; Path={COOKIE_PATH}; SameSite=Lax{secure}"
    by_id("cookie-warning").hidden = read_cookie_text() == saves_text(savestates)
def serialize_save():
    latest = None
    for medal in medal_widgets:
        if not medal.is_collected: break
        latest = medal.key
    achs = ", ".join(f"ach{a.key}" for a in achievement_widgets if a.is_collected)
    return f"{latest or 'None'}; {achs or 'None'}"
def parse_save(line):
    medal_part, _, ach_part = line.partition(";")
    medal = medal_part.strip()
    tokens = (t.strip().lower() for t in ach_part.split(","))
    return (medal if medal in MEDAL_KEYS else None), [int(t[3:]) for t in tokens if t.startswith("ach") and t[3:].isdigit()]
def save_preview(line):
    medal, achs = parse_save(line)
    if medal is None and not achs: return "Empty Save\n0 Achievements"
    return f"Latest medal: Medal {medal or 'None'}\n{len(achs)} Achievement(s)"
# Every save can grow to this size, so the number of save files is capped to keep the cookie under the browser limit
LONGEST_SAVE = f"{MEDAL_KEYS[-1]}; " + ", ".join(f"ach{a.key}" for a in achievement_widgets)
MAX_SAVES = max(1, COOKIE_MAX_BYTES // len(encode_saves([LONGEST_SAVE])))
def save_current(*_):
    if 0 <= state.current_save < len(savestates):
        savestates[state.current_save] = serialize_save()
        write_saves()
def schedule_autosave():
    if state.autosave_job is not None: clear_timeout(state.autosave_job)
    state.autosave_job = set_timeout(autosave, AUTOSAVE_MS)
def autosave():
    state.autosave_job = None
    save_current()
    refresh_save_list()
    schedule_autosave()
def reset_session():
    state.reset()
    for widget in medal_widgets + achievement_widgets: widget.reset()
    for widget in silver_widgets: widget.milestone_btn.disabled = True
    for btn in bg_buttons: btn.hidden = True
    update_bg("default")
    reset_digit_buttons()
def load_save(index):
    state.loading, state.current_save = True, index
    reset_session()
    last_medal, ach_numbers = parse_save(savestates[index])
    if last_medal:
        last_index = MEDAL_KEYS.index(last_medal)
        for medal in medal_widgets[:last_index + 1]:
            medal.set_enabled()
            medal.collect()
        state.value = medal_widgets[last_index].at  # Resume at the last medal's number
    check_silver_unlock()
    for number in ach_numbers:
        if 1 <= number <= len(achievement_widgets): achievement_widgets[number - 1].collect()
    state.loading = False
    refresh_stats()
    update_main()  # Also marks every achievement already passed as missed
    for btn in LOCKED_UNTIL_SAVE_LOADED: btn.disabled = False
    refresh_save_list()
    schedule_autosave()
    show_screen("game")
def create_save():
    if len(savestates) >= MAX_SAVES:
        custom_msg_box("SAVE LIMIT REACHED", f"You can keep up to {MAX_SAVES} save files. Delete one to make room for a new one.")
        return
    savestates.append("None; None")
    write_saves()
    load_save(len(savestates) - 1)
    custom_msg_box("INTRODUCTION TO NUMBERS", INTRO_TEXT)
def delete_save(index):
    if not 0 <= index < len(savestates): return
    savestates.pop(index)
    write_saves()
    if state.current_save > index: state.current_save -= 1
    refresh_save_list()
def refresh_save_list():
    rows = []
    for index, line in enumerate(savestates):
        if ";" not in line: continue
        row = el("div", "save-row")
        row.append(el("button", text="✔️", type="button", title="Load this save", data_action="load", data_index=index),
                   el("div", "save-preview", save_preview(line)),
                   delete_btn := el("button", text="🗑️", type="button", title="Delete this save", data_action="delete", data_index=index))
        delete_btn.disabled = index == state.current_save
        rows.append(row)
    save_rows.replaceChildren(*rows)
def quit_game():  # A web page can't close its own tab, so: save, then go back to the start-up state
    if state.current_save < 0: return
    save_current()
    if state.autosave_job is not None: clear_timeout(state.autosave_job)
    state.autosave_job, state.current_save = None, -1
    reset_session()
    refresh_stats()
    update_main()
    for btn in LOCKED_UNTIL_SAVE_LOADED: btn.disabled = True
    refresh_save_list()
    show_screen("settings")
    custom_msg_box("GAME CLOSED", "Your progress has been saved. You can close this tab, or load a save to keep playing.")
# A tab can be closed at any moment, so also save whenever the page is hidden or left
on(document, "visibilitychange", lambda e: save_current() if document.visibilityState == "hidden" else None)
on(window, "pagehide", save_current)

# =====================================================================
# 10. MUSIC PLAYER
# =====================================================================

audio = document.createElement("audio")
audio.preload = "auto"
audio.id = "music-audio"
document.body.appendChild(audio)  # Hidden (no controls); the panel's buttons drive it
music =SimpleNamespace(tracks=[], index=0, loop=False)
music_url, music_status, music_tracks = by_id("music-url"), by_id("music-status"), by_id("music-tracks")
music_toggle, music_stop, music_loop, music_volume = by_id("music-toggle"), by_id("music-stop"), by_id("music-loop"), by_id("music-volume")

def set_music_status(text): music_status.textContent = text
def track_name(url):
    try:
        name = str(js.decodeURIComponent(js.URL.new(url).pathname.rstrip("/").split("/")[-1]))
        return name or url
    except Exception: return url
def resolve_url(raw, base):
    try: return str(js.URL.new(raw, base).href)
    except Exception: return None
def find_audio_on_page(text, base, content_type):
    """Every audio source on a fetched page: <audio>/<video> sources, og:audio tags, links to audio files and podcast enclosures."""
    doc = js.DOMParser.new().parseFromString(text, "application/xml" if "xml" in content_type and "html" not in content_type else "text/html")
    found = []
    def add(raw):
        url = resolve_url(raw, base) if raw else None
        if url and url not in found: found.append(url)
    for node in doc.querySelectorAll("audio[src], video[src], audio source[src], video source[src]"): add(node.getAttribute("src"))
    for node in doc.querySelectorAll("meta[property^='og:audio'][content], meta[name='twitter:player:stream'][content]"): add(node.getAttribute("content"))
    for node in doc.querySelectorAll("enclosure[url]"): add(node.getAttribute("url"))
    for node in doc.querySelectorAll("a[href]"):
        href = node.getAttribute("href") or ""
        if href.split("?")[0].split("#")[0].lower().endswith(AUDIO_EXTENSIONS): add(href)
    return found
def set_tracks(urls):
    music.tracks = urls
    options = [el("option", text=f"{i + 1}. {track_name(u)}", value=i) for i, u in enumerate(urls)]
    music_tracks.replaceChildren(*options)
    music_tracks.hidden = len(urls) < 2
    play_track(0)
def play_track(index):
    music.index = index
    music_tracks.value = str(index)
    audio.src = music.tracks[index]
    audio.loop = music.loop
    set_music_status(f"Loading {track_name(music.tracks[index])}...")
    start_playback()
def start_playback():
    def failed(err):
        if getattr(err, "name", "") == "NotAllowedError": set_music_status("Press Play to start the music.")
    audio.play().catch(create_once_callable(failed))
async def load_music(raw):
    url = resolve_url(raw.strip(), window.location.href) if raw.strip() else None
    if not url or not url.lower().startswith(("http://", "https://")):
        set_music_status("Enter a web link (starting with https://).")
        return
    if js.URL.new(url).pathname.lower().endswith(AUDIO_EXTENSIONS):  # A direct link to an audio file
        set_tracks([url])
        return
    set_music_status("Looking for audio...")
    controller = js.AbortController.new()
    try:
        response = await js.fetch(url, to_js({"signal": controller.signal}, dict_converter=js.Object.fromEntries))
    except Exception:  # Most sites don't let other sites read their pages; the link may still be playable audio
        set_tracks([url])
        return
    if not response.ok:
        set_music_status(f"That link didn't work (the site answered with error {response.status}).")
        return
    content_type = str(response.headers.get("content-type") or "").lower()
    if "html" in content_type or "xml" in content_type:
        tracks = find_audio_on_page(str(await response.text()), str(response.url), content_type)
        if tracks: set_tracks(tracks)
        else: set_music_status("No playable audio was found on that page.")
    else:
        controller.abort()  # Audio files are streamed by the player itself, so stop this download
        set_tracks([url])
def on_audio_error(event):
    if not audio.getAttribute("src"): return
    set_music_status("Couldn't play that link. If it's a web page, that site doesn't let other sites read it - try a direct link to the audio file instead.")
    music_toggle.disabled = music_stop.disabled = True
def on_audio_ended(event):
    if not music.loop and music.index + 1 < len(music.tracks): play_track(music.index + 1)
    else: refresh_music_buttons()
def refresh_music_buttons(*_):
    has_track = bool(audio.getAttribute("src")) and not audio.error
    music_toggle.disabled = music_stop.disabled = not has_track
    music_toggle.textContent = "Play" if audio.paused else "Pause"
    music_loop.textContent = f"Loop: {'On' if music.loop else 'Off'}"
    music_loop.classList.toggle("selected", music.loop)
def toggle_music():
    if audio.paused: start_playback()
    else: audio.pause()
def stop_music():
    audio.pause()
    audio.currentTime = 0
    set_music_status("Stopped.")
def toggle_loop():
    music.loop = not music.loop
    audio.loop = music.loop
    refresh_music_buttons()

on(by_id("music-load"), "click", lambda e: asyncio.ensure_future(load_music(music_url.value)))
on(music_url, "keydown", lambda e: asyncio.ensure_future(load_music(music_url.value)) if e.key == "Enter" else None)
on(music_tracks, "change", lambda e: play_track(int(music_tracks.value)))
on(music_toggle, "click", lambda e: toggle_music())
on(music_stop, "click", lambda e: stop_music())
on(music_loop, "click", lambda e: toggle_loop())
on(music_volume, "input", lambda e: setattr(audio, "volume", int(music_volume.value) / 100))
on(audio, "playing", lambda e: (set_music_status(f"Now playing: {track_name(music.tracks[music.index])}"), refresh_music_buttons()))
on(audio, "pause", lambda e: (set_music_status("Finished." if audio.ended else "Paused.") if audio.currentTime > 0 else None, refresh_music_buttons()))
on(audio, "error", on_audio_error)
on(audio, "ended", on_audio_ended)
music_volume.value = str(MUSIC_DEFAULT_VOLUME)
audio.volume = MUSIC_DEFAULT_VOLUME / 100
refresh_music_buttons()

# =====================================================================
# 11. MAIN ENTRY POINT
# =====================================================================

savestates = read_saves()
if not window.navigator.cookieEnabled: by_id("cookie-warning").hidden = False
refresh_stats()
update_bg(view.background)
show_screen("settings")
update_main()
refresh_save_list()

by_id("cookie-notice-title").innerHTML = COOKIE_NOTICE_TITLE
by_id("cookie-notice-text").innerHTML = COOKIE_NOTICE_TEXT
by_id("cookie-notice").hidden = False
on(by_id("cookie-notice-ok"), "click", lambda e: setattr(by_id("cookie-notice"), "hidden", True))
by_id("cookie-notice-ok").focus()
loading_screen = by_id("loading")
if loading_screen: loading_screen.remove()
