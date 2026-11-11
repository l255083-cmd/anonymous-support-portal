# Anonymous Support and Advice Portal
# Programming Lab - Assignment 3

import json
import random

DATA_FILE = "portal_data.json"
LOG_FILE = "activity_log.txt"
REPORT_FILE = "portal_report.txt"

BOTTLE_TYPES = ("advice", "comfort", "motivation")
MOODS = ("sad", "stressed", "confused", "lost", "anxious", "lonely", "other")
FIRST_NAMES = ("Quiet", "Lost", "Silver", "Gentle", "Calm", "Hidden", "Blue")
SECOND_NAMES = ("Wave", "Anchor", "Shell", "Tide", "Pearl", "Gull")
DANGER_WORDS = ("suicide", "kill myself", "end my life", "want to die", "self harm")

CATCH_LIMIT = 3       # how many bottles a user can catch in one login
LIGHTHOUSE_LIMIT = 3  # helpful replies needed to become a Lighthouse


def load_data(filename):
    """Reads all portal data from the JSON file. Returns the data dictionary."""
    data = {"tide": 0, "users": [], "bottles": [], "replies": [], "reports": []}
    file = None
    try:
        file = open(filename, "r")
        data = json.load(file)
        print("Data loaded from", filename)
    except FileNotFoundError:
        print("No data file found. Starting fresh with some demo data.")
        add_demo_data(data)
    except PermissionError:
        print("Error: not allowed to open", filename)
    except json.JSONDecodeError:
        print("Error: the data file is damaged. Starting with empty data.")
    finally:
        if file != None:
            file.close()

    # make sure no part of the data is missing
    for key in ["users", "bottles", "replies", "reports"]:
        if key not in data:
            data[key] = []
    if "tide" not in data:
        data["tide"] = 0
    return data


def save_data(data, filename):
    """Writes all portal data to the JSON file. Returns True if it worked."""
    file = None
    try:
        file = open(filename, "w")
        json.dump(data, file, indent=4)
        return True
    except PermissionError:
        print("Error: not allowed to save to", filename)
        return False
    finally:
        if file != None:
            file.close()


def write_log(message):
    """Adds one line to the activity log (append mode). Returns True if it worked."""
    try:
        file = open(LOG_FILE, "a")
        file.write(message + "\n")
        file.close()
        return True
    except PermissionError:
        print("Error: could not write to the log file")
        return False


def check_number(text, low, high):
    """Changes text into a number between low and high. Returns the number, or None if it is not valid."""
    try:
        number = int(text)
    except ValueError:
        print("Please enter a number, not letters.")
        return None
    if number < low or number > high:
        print("Please enter a number from", low, "to", high)
        return None
    return number


def get_number(question, low, high):
    """Keeps asking until the user types a valid number. Returns the number."""
    while True:
        text = input(question)
        number = check_number(text, low, high)
        if number != None:
            return number


def choose_from(options, title):
    """Shows a numbered list of options. Returns the option the user picks."""
    print(title)
    for i in range(len(options)):
        print(f"  {i + 1}. {options[i]}")
    choice = get_number("Your choice: ", 1, len(options))
    return options[choice - 1]


def find_user(data, username):
    """Finds a user by username. Returns the user, or None."""
    for user in data["users"]:
        if user["username"] == username:
            return user
    return None


def find_by_id(items, item_id):
    """Finds a user, bottle or reply by its id. Returns the item, or None."""
    for item in items:
        if item["id"] == item_id:
            return item
    return None


def make_alias(data):
    """Makes a random anonymous name that nobody else has. Returns the name."""
    while True:
        alias = random.choice(FIRST_NAMES) + " " + random.choice(SECOND_NAMES) + " " + str(random.randint(10, 99))
        taken = False
        for user in data["users"]:
            if user["alias"] == alias:
                taken = True
        if taken == False:
            return alias


def has_danger_words(message):
    """Checks if a message has any danger words. Returns True or False."""
    for word in DANGER_WORDS:
        if word in message.lower():
            return True
    return False


def register_user(data, username, password):
    """Creates a new account. Returns True if the account was made."""
    if username == "" or " " in username:
        print("Username cannot be empty or have spaces.")
        return False
    if len(password) < 4:
        print("Password must be at least 4 characters.")
        return False
    if find_user(data, username) != None:
        print("This username is already taken.")
        return False

    user = {
        "id": len(data["users"]) + 1,
        "username": username,
        "password": password,
        "alias": make_alias(data),
        "helped": 0,
    }
    data["users"].append(user)
    write_log("New user joined as " + user["alias"])
    print("Account created! Other people will only see you as:", user["alias"])
    return True


def user_login(data, username, password):
    """Checks the username and password. Returns the user if correct, otherwise None."""
    user = find_user(data, username)
    if user == None or user["password"] != password:
        print("Wrong username or password.")
        return None
    write_log(user["alias"] + " logged in")
    print("Welcome back,", user["alias"])
    return user


def throw_bottle(data, user, bottle_type, mood, message):
    """Adds a new bottle to the sea (our add record function). Returns True if it was added."""
    if bottle_type not in BOTTLE_TYPES or mood not in MOODS:
        print("Wrong bottle type or mood.")
        return False
    if len(message) < 10:
        print("Message is too short, please write a bit more.")
        return False

    bottle = {
        "id": len(data["bottles"]) + 1,
        "sender_id": user["id"],
        "type": bottle_type,
        "mood": mood,
        "message": message,
        "status": "drifting",
        "ready_at": data["tide"] + random.randint(1, 3),
        "touched": 0,
        "caught_by": [],
    }
    data["bottles"].append(bottle)
    write_log(user["alias"] + " threw bottle " + str(bottle["id"]))
    print("Your bottle is drifting out to sea...")

    if has_danger_words(message):
        print("It sounds like you are going through something very hard.")
        print("Please talk to someone you trust or call a mental health helpline.")
    return True


def find_catchable(data, user):
    """Returns a list of bottles that this user is allowed to catch."""
    catchable = []
    for bottle in data["bottles"]:
        if bottle["status"] == "drifting":
            if bottle["sender_id"] != user["id"]:
                if bottle["ready_at"] <= data["tide"]:
                    if user["id"] not in bottle["caught_by"]:
                        catchable.append(bottle)
    return catchable


def catch_bottle(data, user):
    """Picks a random bottle from the shore. Returns the bottle, or None if there are none."""
    catchable = find_catchable(data, user)
    if len(catchable) == 0:
        return None
    bottle = random.choice(catchable)
    bottle["touched"] = bottle["touched"] + 1
    bottle["caught_by"].append(user["id"])
    write_log(user["alias"] + " caught bottle " + str(bottle["id"]))
    return bottle


def reply_bottle(data, user, bottle, text):
    """Saves a reply to a bottle. Returns True if the reply was saved."""
    if bottle["status"] != "drifting":
        print("Someone already replied to this bottle.")
        return False
    if len(text) < 10:
        print("Reply is too short, please write a bit more.")
        return False

    reply = {
        "id": len(data["replies"]) + 1,
        "bottle_id": bottle["id"],
        "replier_id": user["id"],
        "message": text,
        "helpful": False,
    }
    data["replies"].append(reply)
    bottle["status"] = "replied"
    write_log(user["alias"] + " replied to bottle " + str(bottle["id"]))
    print("Your reply is floating back to them. Thank you for being kind!")
    return True


def throw_back(data, bottle):
    """Lets a bottle drift again so someone else can catch it. Returns its new ready time."""
    bottle["ready_at"] = data["tide"] + random.randint(1, 3)
    write_log("Bottle " + str(bottle["id"]) + " was thrown back")
    print("You let the bottle drift away.")
    return bottle["ready_at"]


def get_my_bottles(data, user):
    """Returns a list of the user's bottles. Each item is a tuple (bottle, replies)."""
    my_bottles = []
    for bottle in data["bottles"]:
        if bottle["sender_id"] == user["id"]:
            replies = []
            for reply in data["replies"]:
                if reply["bottle_id"] == bottle["id"]:
                    replies.append(reply)
            my_bottles.append((bottle, replies))
    return my_bottles


def mark_helpful(data, user, reply_id):
    """Marks a reply on the user's own bottle as helpful. Returns True if it worked."""
    reply = find_by_id(data["replies"], reply_id)
    if reply == None:
        print("There is no reply with that number.")
        return False
    bottle = find_by_id(data["bottles"], reply["bottle_id"])
    if bottle["sender_id"] != user["id"]:
        print("You can only rate replies to your own bottles.")
        return False
    if reply["helpful"] == True:
        print("You already marked this reply as helpful.")
        return False

    reply["helpful"] = True
    helper = find_by_id(data["users"], reply["replier_id"])
    helper["helped"] = helper["helped"] + 1
    write_log(helper["alias"] + "'s reply was marked helpful")
    print("Thanks! We told", helper["alias"], "that their reply helped.")
    if helper["helped"] == LIGHTHOUSE_LIMIT:
        print(helper["alias"], "is now a Lighthouse!")
    return True


def report_reply(data, user, reply_id, reason):
    """Reports a bad reply. Returns True if the report was saved."""
    if find_by_id(data["replies"], reply_id) == None:
        print("There is no reply with that number.")
        return False
    if reason == "":
        print("Please write a reason.")
        return False

    report = {
        "id": len(data["reports"]) + 1,
        "reply_id": reply_id,
        "reporter_id": user["id"],
        "reason": reason,
    }
    data["reports"].append(report)
    write_log("Reply " + str(reply_id) + " was reported")
    print("Thank you, the reply has been reported.")
    return True


def search_bottles(data, keyword, bottle_type, mood):
    """Finds bottles matching the keyword, type and mood (our search record function).
    An empty value means any. Returns a list of matching bottles."""
    results = []
    for bottle in data["bottles"]:
        match = True
        if keyword != "" and keyword.lower() not in bottle["message"].lower():
            match = False
        if bottle_type != "" and bottle["type"] != bottle_type:
            match = False
        if mood != "" and bottle["mood"] != mood:
            match = False
        if match == True:
            results.append(bottle)
    return results


def get_leaderboard(data):
    """Returns users who helped someone, sorted from most to least helpful."""
    helpers = []
    for user in data["users"]:
        if user["helped"] > 0:
            helpers.append(user)

    # bubble sort
    for i in range(len(helpers)):
        for j in range(len(helpers) - 1 - i):
            if helpers[j]["helped"] < helpers[j + 1]["helped"]:
                temp = helpers[j]
                helpers[j] = helpers[j + 1]
                helpers[j + 1] = temp
    return helpers


def generate_report(data):
    """Counts statistics about the portal, saves them in a text file and returns the report."""
    type_count = {}
    for bottle_type in BOTTLE_TYPES:
        type_count[bottle_type] = 0
    mood_count = {}
    for mood in MOODS:
        mood_count[mood] = 0

    replied = 0
    for bottle in data["bottles"]:
        type_count[bottle["type"]] = type_count[bottle["type"]] + 1
        mood_count[bottle["mood"]] = mood_count[bottle["mood"]] + 1
        if bottle["status"] == "replied":
            replied = replied + 1

    helpful = 0
    for reply in data["replies"]:
        if reply["helpful"] == True:
            helpful = helpful + 1

    top_mood = "none"
    top_number = 0
    for mood in mood_count:
        if mood_count[mood] > top_number:
            top_mood = mood
            top_number = mood_count[mood]

    total = len(data["bottles"])
    if total > 0:
        percent = round(replied / total * 100)
    else:
        percent = 0

    report = "========== PORTAL REPORT ==========\n"
    report = report + f"Users: {len(data['users'])}\n"
    report = report + f"Bottles thrown: {total}\n"
    report = report + f"Bottles answered: {replied} ({percent}%)\n"
    report = report + f"Replies written: {len(data['replies'])}\n"
    report = report + f"Helpful replies: {helpful}\n"
    report = report + f"Reported replies: {len(data['reports'])}\n"
    report = report + "Bottles by type:\n"
    for bottle_type in type_count:
        report = report + f"   {bottle_type}: {type_count[bottle_type]}\n"
    report = report + f"Most common mood: {top_mood}\n"
    report = report + "Top helpers:\n"
    leaderboard = get_leaderboard(data)
    if len(leaderboard) == 0:
        report = report + "   nobody yet\n"
    count = 0
    for user in leaderboard:
        if count < 3:
            report = report + f"   {count + 1}. {user['alias']} ({user['helped']} helpful)\n"
            count = count + 1

    file = None
    try:
        file = open(REPORT_FILE, "w")
        file.write(report)
    except PermissionError:
        print("Error: could not save the report file")
    finally:
        if file != None:
            file.close()
    return report


def add_demo_data(data):
    """Adds two demo users and three bottles. Returns the number of bottles added."""
    register_user(data, "ayesha", "1234")
    register_user(data, "bilal", "1234")
    ayesha = find_user(data, "ayesha")
    bilal = find_user(data, "bilal")

    throw_bottle(data, ayesha, "motivation", "stressed", "Exams start next week and I feel like I already failed.")
    throw_bottle(data, bilal, "comfort", "lonely", "I moved to a new city for uni and I have no friends here yet.")
    throw_bottle(data, ayesha, "advice", "confused", "Should I tell my parents I want to change my degree?")

    # demo bottles can be caught straight away
    for bottle in data["bottles"]:
        bottle["ready_at"] = 0
    return len(data["bottles"])


def throw_menu(data, user):
    """Asks the user for a bottle and throws it."""
    bottle_type = choose_from(BOTTLE_TYPES, "What do you need?")
    mood = choose_from(MOODS, "How are you feeling?")
    message = input("Write your message: ").strip()
    throw_bottle(data, user, bottle_type, mood, message)


def catch_menu(data, user, catches_left):
    """Catches a bottle and lets the user reply or throw it back. Returns catches left."""
    if catches_left == 0:
        print("You caught enough bottles for now. Come back later.")
        return 0
    bottle = catch_bottle(data, user)
    if bottle == None:
        print("The shore is empty right now. No bottles have washed up.")
        return catches_left

    print("A bottle washed up at your feet!")
    print("Needs:", bottle["type"], "| Mood:", bottle["mood"])
    print("Message:", bottle["message"])
    if bottle["touched"] > 1:
        print(bottle["touched"] - 1, "other people found this bottle before you.")

    print("1. Reply")
    print("2. Throw it back")
    choice = get_number("Choose: ", 1, 2)
    if choice == 1:
        text = input("Your reply: ").strip()
        saved = reply_bottle(data, user, bottle, text)
        if saved == False:
            throw_back(data, bottle)
    else:
        throw_back(data, bottle)
    return catches_left - 1


def my_bottles_menu(data, user):
    """Shows the user's bottles and replies, and lets them mark helpful or report."""
    my_bottles = get_my_bottles(data, user)
    if len(my_bottles) == 0:
        print("You have not thrown any bottles yet.")
        return

    reply_count = 0
    for bottle, replies in my_bottles:
        print()
        print(f"Bottle {bottle['id']} ({bottle['type']}, {bottle['mood']}) - {bottle['status']}")
        print("  ", bottle["message"])
        for reply in replies:
            helper = find_by_id(data["users"], reply["replier_id"])
            print(f"   Reply {reply['id']} from {helper['alias']}: {reply['message']}")
            if reply["helpful"] == True:
                print("   (you marked this as helpful)")
            reply_count = reply_count + 1

    if reply_count == 0:
        print("No replies yet, your bottles are still drifting.")
        return

    print()
    print("1. Mark a reply as helpful")
    print("2. Report a reply")
    print("3. Go back")
    choice = get_number("Choose: ", 1, 3)
    if choice == 1:
        reply_id = get_number("Reply number: ", 1, len(data["replies"]))
        mark_helpful(data, user, reply_id)
    elif choice == 2:
        reply_id = get_number("Reply number: ", 1, len(data["replies"]))
        reason = input("Why are you reporting it? ").strip()
        report_reply(data, user, reply_id, reason)


def search_menu(data):
    """Asks for search filters and shows the matching bottles."""
    keyword = input("Search word (press Enter to skip): ").strip()
    bottle_type = input("Type - advice, comfort or motivation (press Enter to skip): ").strip().lower()
    mood = input("Mood (press Enter to skip): ").strip().lower()
    results = search_bottles(data, keyword, bottle_type, mood)
    print("Found", len(results), "bottle(s)")
    for bottle in results:
        print(f"  Bottle {bottle['id']} ({bottle['type']}, {bottle['mood']}, {bottle['status']}): {bottle['message']}")


def leaderboard_menu(data):
    """Prints the Lighthouse leaderboard."""
    helpers = get_leaderboard(data)
    if len(helpers) == 0:
        print("Nobody has been marked helpful yet.")
        return
    rank = 1
    for user in helpers:
        if user["helped"] >= LIGHTHOUSE_LIMIT:
            print(f"{rank}. {user['alias']} - helpful replies: {user['helped']} - LIGHTHOUSE")
        else:
            print(f"{rank}. {user['alias']} - helpful replies: {user['helped']}")
        rank = rank + 1


def user_menu(data, user):
    """Menu for a logged in user. Keeps running until the user logs out."""
    catches_left = CATCH_LIMIT
    while True:
        print()
        print("=====", user["alias"], "=====")
        print("1. Throw a bottle")
        print("2. Catch a bottle (" + str(catches_left) + " left)")
        print("3. My bottles and replies")
        print("4. Search bottles")
        print("5. Lighthouse leaderboard")
        print("6. Generate report")
        print("7. Logout")
        choice = get_number("Choose: ", 1, 7)

        if choice == 7:
            write_log(user["alias"] + " logged out")
            print("Logged out. Take care!")
            break

        data["tide"] = data["tide"] + 1
        if choice == 1:
            throw_menu(data, user)
        elif choice == 2:
            catches_left = catch_menu(data, user, catches_left)
        elif choice == 3:
            my_bottles_menu(data, user)
        elif choice == 4:
            search_menu(data)
        elif choice == 5:
            leaderboard_menu(data)
        elif choice == 6:
            print(generate_report(data))
            print("Report saved in", REPORT_FILE)
        save_data(data, DATA_FILE)


def main():
    """Starts the portal: loads the data, shows the main menu and saves when finished."""
    data = load_data(DATA_FILE)
    print("==========================================")
    print("   ANONYMOUS SUPPORT AND ADVICE PORTAL")
    print("   Say it to the sea. Someone will answer.")
    print("==========================================")
    try:
        while True:
            print()
            print("1. Register")
            print("2. Login")
            print("3. Exit")
            choice = get_number("Choose: ", 1, 3)
            if choice == 1:
                username = input("Choose a username: ").strip()
                password = input("Choose a password: ")
                register_user(data, username, password)
                save_data(data, DATA_FILE)
            elif choice == 2:
                username = input("Username: ").strip()
                password = input("Password: ")
                user = user_login(data, username, password)
                if user != None:
                    user_menu(data, user)
            else:
                print("Goodbye! Take care.")
                break
    except KeyboardInterrupt:
        print("Portal stopped.")
    finally:
        save_data(data, DATA_FILE)
        print("All data saved.")


main()
