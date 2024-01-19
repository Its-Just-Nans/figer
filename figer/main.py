"""function useful for figer"""
from os.path import expanduser, join, isdir, isfile, basename, abspath
from os import mkdir, scandir
import argparse
import traceback
import logging
import readline
from datetime import datetime
from json import loads, dumps
from .__version__ import __version__

home = expanduser("~")
PROGRAM_NAME = "figer"
FOLDER_FIGER = join(home, f".{PROGRAM_NAME}")
CONF_FILE = join(FOLDER_FIGER, "config.json")
VERSION = __version__
logging.basicConfig(level=logging.INFO)
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
        self.load()

    def create(self, creation=True):
        """create config file"""
        if creation:
            LOG.info("No config file detected")
            LOG.info("Creating a new config now")
        registering = True
        while registering:
            to_save = input("Enter the path to be saved (or 'quit' to exit):\n")
            if to_save == "quit":
                registering = False
            else:
                if not to_save.startswith("/"):
                    to_save = abspath(to_save)
                if to_save in self.paths:
                    LOG.info("Path already registered !")
                else:
                    if isfile(to_save):
                        self.paths[to_save] = clean_path(to_save)
                    else:
                        LOG.info("File '%s' does not exists", to_save)
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

    def save(self, new_users=None, new_paths=None):
        """write config file"""
        if new_users is not None:
            self.users = new_users
        if new_paths is not None:
            self.paths = new_paths
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
                print(
                    f"Directory '{one_subfolder}/' is present but it's not in the config !"
                )
                need_add = input("Should we had it ? [Y/n]\n").lower()
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
    print("This CLI let you save and load you config files")
    print("It can be useful for multi user system")
    print("")
    parse_args().print_help()
    print(f"{PROGRAM_NAME} - v{VERSION}")


class Figer:
    """main class of CLI"""

    def __init__(self, args=None) -> None:
        if args is None:
            print_info()
            return
        if "command" in args:
            if args["command"] == "save":
                self.save(args["username"])
            elif args["command"] == "load":
                self.load(args["username"])
            elif args["command"] == "show":
                self.show_config()
            elif args["command"] == "check":
                self.check()
            elif args["command"] == "edit":
                self.edit_config()
            else:
                print_info()
        else:
            print_info()

    def _change_access_time(self, username):
        """change the access time"""
        c = ConfigFile().get_config()
        if username not in c["users"]:
            c["users"][username] = {}
        c["users"][username]["last_access"] = datetime.now().strftime(
            "%Y-%m-%d_%H-%M-%S"
        )
        ConfigFile().save(new_users=c["users"])

    def save(self, username):
        """Save the current profile"""
        c = ConfigFile().get_config()
        self._change_access_time(username)
        LOG.info("Saving the profile %s", username)
        path_to_user = join(FOLDER_FIGER, username)
        if not isdir(path_to_user):
            mkdir(path_to_user)
        for path_computer, local_path in c["paths"].items():
            path_to_save = join(path_to_user, local_path)
            LOG.debug("Saving %s", path_computer)
            self._copy_file(path_computer, path_to_save)
            LOG.info("Saved %s to %s", path_computer, path_to_save)
        # to do add user to config and save access time

    def load(self, username):
        """load the profile"""
        c = ConfigFile().get_config()
        LOG.info("Loading the profile %s", username)
        for one_user in c["users"]:
            if one_user == username:
                LOG.debug("Loading %s", username)
                self._change_access_time(username)
                self.load_files(one_user, c["paths"])
                return
        LOG.error("user %s does not exists", username)

    def _copy_file(self, source, dest):
        """copy a file"""
        try:
            with open(source, "rb") as file:
                file_content = file.read()
                with open(dest, "wb") as file_to_write:
                    file_to_write.write(file_content)
        except Exception as e:
            LOG.error("Error during copying %s to %s: %s", source, dest, str(e))

    def load_files(self, user, files):
        """load the files"""
        for path_computer, file_path_local in files.items():
            path_local = join(FOLDER_FIGER, user, file_path_local)
            LOG.debug("Loading '%s'", path_computer)
            if not isfile(path_local):
                LOG.warning("File '%s' does not exists, skipping", path_local)
                continue
            self._copy_file(path_local, path_computer)

    def show_config(self):
        """show config"""
        ConfigFile().print_config()

    def edit_config(self):
        """Configure figer"""
        choice = input("Remove (1) or add (2) a path ?\n")
        if choice == "1":
            c = ConfigFile().get_config()
            if len(c["paths"]) == 0:
                LOG.info("No path to remove")
                return
            to_delete = []
            for one_path in c["paths"]:
                test = input(f"Remove {one_path} ? [y/N]").lower()
                if test == "y" or test == "yes":
                    to_delete.append(one_path)
            if len(to_delete) != 0:
                for one_path in to_delete:
                    del c["paths"][one_path]
                ConfigFile().save(new_paths=c["paths"])
            return
        elif choice == "2":
            ConfigFile().create(creation=False)
        LOG.info("Config edited")

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
    subparsers.add_parser("check", help="Check config")
    subparsers.add_parser("edit", help="Edit config")
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug mode")
    return parser


def main():
    """Main entry point for the figer CLI."""
    debug = False
    try:
        readline.parse_and_bind("tab: complete")
        args = parse_args().parse_args()
        debug = args.debug
        if debug:
            LOG.setLevel(logging.DEBUG)
        # convert to dict for easier use of figer as external package
        Figer(vars(args))
    except KeyboardInterrupt:
        LOG.info("Exiting figer")
        exit(0)
    except Exception as e:
        LOG.error("Error during execution: %s", str(e))
        if debug:
            print(traceback.format_exc())
        exit(1)
