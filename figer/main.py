"""function useful for figer"""
from os.path import expanduser, join, isdir, isfile, basename
from os import mkdir, scandir
import argparse
import logging
from json import loads, dumps

home = expanduser("~")
PROGRAM_NAME = "figer"
FOLDER_FIGER = join(home, f".{PROGRAM_NAME}")
CONF_FILE = join(FOLDER_FIGER, "config.json")
VERSION = "1.0.0"
logging.basicConfig(level=logging.DEBUG)
LOG = logging.getLogger(PROGRAM_NAME)


def clean_path(path):
    """convert to ascii"""
    return "".join([i if (i.isalnum() or i == ".") else "_" for i in path])


class ConfigFile:
    """config file class"""

    paths = {}
    users = {}

    def __init__(self) -> None:
        """init"""
        self.check()
        self.load()

    def create(self):
        """create config file"""
        LOG.info("No config file detected")
        LOG.info("Creating a new config now")
        registering = True
        while registering:
            to_save = input("Enter the path to be saved (or 'quit' to exit):\n")
            if to_save == "quit":
                registering = False
            else:
                if isfile(to_save):
                    self.paths[to_save] = clean_path(to_save)
                else:
                    LOG.info("File %s does not exists", to_save)
        self.save()

    def load(self):
        """load the conf file"""
        if not isdir(FOLDER_FIGER):
            mkdir(FOLDER_FIGER)
        if isfile(CONF_FILE):
            try:
                with open(CONF_FILE, "r", encoding="utf-8") as file:
                    readed = file.read()
                    conf = loads(readed)
                    self.paths = conf["paths"]
                    self.users = conf["users"]
                return True
            except Exception as e:
                LOG.warning(
                    "Error during loading the configuration at %s: %s",
                    CONF_FILE,
                    str(e),
                )
                do_try = input(
                    "Try to force create the file (may override infos) [Y/n]"
                )
                do_try = do_try.lower()
                if do_try == "n" or do_try == "no":
                    LOG.info("Didn't try to recreate")
                    return False
                self.save()
                return False
        self.create()
        return True

    def save(self):
        """write config file"""
        if not isdir(FOLDER_FIGER):
            mkdir(FOLDER_FIGER)
        with open(CONF_FILE, "w", encoding="utf-8") as file:
            file.write(dumps(self.get_config(), indent=4))

    def check(self):
        """check if there is a config file"""
        self.load()
        for one_user in self.users:
            if not isdir(join(FOLDER_FIGER, one_user)):
                LOG.info(
                    "User %s is in the conf but there are no directory related to him",
                    one_user,
                )
                # TODO create
        subfolders = [basename(f.path) for f in scandir(FOLDER_FIGER) if f.is_dir()]
        for one_subfolder in subfolders:
            if one_subfolder not in self.users:
                need_add = input(
                    f"User {one_subfolder} has a directory but is not in the config, do we had it ? [Y/n]\n"
                ).lower()
                if need_add == "n" or need_add == "no":
                    continue
                self.users[one_subfolder] = {}
                self.save()

    def get_config(self):
        """get the config"""
        return {"users": self.users, "paths": self.paths}

    def print_config(self):
        """print the config"""
        print(dumps(self.get_config(), indent=4))


def print_info():
    """print the info"""
    print(f"Welcome to {PROGRAM_NAME}")
    print(
        "This CLI let's you save and load you config files. It can be useful for multi user system"
    )
    parse_args().print_help()
    print(f"{PROGRAM_NAME} - v{VERSION}")


class Figer:
    """main class of CLI"""

    def __init__(self, args) -> None:
        ConfigFile().check()
        if args.command == "save":
            self.save(args.username)
        elif args.command == "load":
            self.load(args.username)
        elif args.command == "show":
            self.show_config()
        else:
            print_info()

    def save(self, username):
        """Save the current profile"""
        c = ConfigFile().get_config()
        LOG.info("Saving the profile %s", username)
        path_to_user = join(FOLDER_FIGER, username)
        if not isdir(path_to_user):
            mkdir(path_to_user)
        for path_computer, local_path in c["paths"].items():
            path_to_save = join(path_to_user, local_path)
            LOG.debug("Saving %s", path_computer)
            with open(path_computer, "rb") as file:
                file_content = file.read()
                with open(path_to_save, "wb") as file_to_write:
                    file_to_write.write(file_content)
            LOG.info("Saved %s to %s", path_computer, path_to_save)
        # to do add user to config and save access time

    def load(self, username):
        """load the profile"""
        c = ConfigFile().get_config()
        LOG.info("Loading the profile %s", username)
        for one_user in c["users"]:
            if one_user == username:
                LOG.debug("Loading %s", username)
                self.load_files(one_user, c["paths"])
                return
        LOG.error("user %s does not exists", username)

    def load_files(self, user, files):
        """load the files"""
        LOG.info("Loading files of %s", user)
        for path_computer, file_path_local in files.items():
            path_local = join(FOLDER_FIGER, user, file_path_local)
            LOG.debug("Loading of %s", path_computer)
            if not isfile(path_local):
                LOG.warning("File %s does not exists, skipping", path_local)
                continue
            with open(path_local, "rb") as file:
                file_content = file.read()
                with open(path_computer, "wb") as file_to_write:
                    file_to_write.write(file_content)

    def show_config(self):
        """show config"""
        ConfigFile().print_config()

    def config(self):
        """Configure figer"""
        pass

    def check(self):
        """Check the file"""
        ConfigFile().check()


def parse_args():
    """parse the args"""
    parser = argparse.ArgumentParser("figer")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    # Load command
    load_parser = subparsers.add_parser("load", help="Load a user")
    load_parser.add_argument("username", type=str, help="Username to load")
    # Save command
    save_parser = subparsers.add_parser("save", help="Save a user")
    save_parser.add_argument("username", type=str, help="Username to save")
    # Show command
    subparsers.add_parser("show", help="Show all users")
    return parser


def main():
    """Main entry point for the figer CLI."""
    try:
        args = parse_args().parse_args()
        Figer(args)
    except KeyboardInterrupt:
        LOG.info("Exiting figer")
        exit(0)
    except Exception as e:
        LOG.error("Error during execution: %s", str(e))
        exit(1)
