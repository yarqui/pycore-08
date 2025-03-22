from functools import wraps
from collections import UserDict
import datetime
import pickle


class Field:
    def __init__(self, value):
        self.value = value

    def __str__(self):
        return str(self.value)


class Name(Field):
    def __init__(self, value):
        if not value or not isinstance(value, str):
            raise ValueError("Name must be a non-empty string")
        super().__init__(value)


class Phone(Field):
    def __init__(self, value):
        value = str(value)

        if len(value) != 10:
            raise ValueError("Phone number should be 10 digits")
        super().__init__(value)


class Birthday(Field):
    def __init__(self, value):
        try:
            date_obj = datetime.datetime.strptime(value, "%d.%m.%Y").date()
            super().__init__(date_obj)
        except ValueError:
            raise ValueError("Invalid date format. Use DD.MM.YYYY")


class Record:
    def __init__(self, name):
        self.name = Name(name)
        self.phones = []
        self.birthday = None

    def add_phone(self, number):
        self.phones.append(Phone(number))

    def delete_phone(self, number):
        number = str(number)
        existing_number = self.find_phone(number)

        if existing_number == None:
            raise ValueError("Phone number was not found")

        self.phones = [p for p in self.phones if p.value != number]

    def update_phone(self, old_number, new_number):
        old_number = str(old_number)

        for i, phone in enumerate(self.phones):
            if phone.value == old_number:
                self.phones[i] = Phone(new_number)
                return

        raise ValueError("Old number was not found")

    def find_phone(self, number):
        number = str(number)
        for phone in self.phones:
            if phone.value == number:
                return phone

        return None

    def add_birthday(self, day):
        if self.birthday:
            raise Exception("Birthday has already been added")

        self.birthday = Birthday(day)

    def __str__(self):
        return f"{self.name.value}, phones: {'; '.join(p.value for p in self.phones)}"


class AddressBook(UserDict):

    def add_record(self, rec):
        self.data[rec.name.value] = rec

    def find_record(self, name):
        return self.data.get(name)

    def delete_record(self, name):
        if name in self.data:
            del self.data[name]

    def get_upcoming_birthdays(self):
        to_greet = []
        today = datetime.date.today()
        week_ahead = today + datetime.timedelta(days=7)

        for record in self.data.values():
            if record.birthday:
                birth_date = record.birthday.value
                birthday_this_year = birth_date.replace(year=today.year)

                if birthday_this_year < today:
                    birthday_this_year = birthday_this_year.replace(year=today.year + 1)

                if today <= birthday_this_year <= week_ahead:
                    # Move weekend birthdays to Monday
                    if birthday_this_year.weekday() >= 5:
                        birthday_this_year += datetime.timedelta(
                            days=(7 - birthday_this_year.weekday())
                        )

                    to_greet.append(
                        {
                            "name": record.name.value,
                            "congratulation_date": birthday_this_year.strftime(
                                "%d.%m.%Y"
                            ),
                        }
                    )

        return to_greet


def input_error(func):
    @wraps(func)
    def inner(*args, **kwargs):
        try:
            return func(*args, **kwargs)

        except IndexError:
            return "Error: Incorrect number of arguments."
        except KeyError:
            return "Error: Contact not found."
        except ValueError as ve:
            return f"Error: {ve}"
        except TypeError as te:
            return f"Error: Invalid input type. {te}"
        except Exception as e:
            return f"Unexpected error: {e}"

    return inner


def parse_input(user_input: str):
    cmd, *args = user_input.strip().casefold().split()
    return cmd, *args


@input_error
def add_contact(args, book: AddressBook):
    name, phone, *_ = args
    record = book.find_record(name)
    message = "Contact updated."
    if record is None:
        record = Record(name)
        book.add_record(record)
        message = "Contact added."
    if phone:
        record.add_phone(phone)
    return message


@input_error
def change_contact(args: list, book: AddressBook):
    if len(args) < 3:
        raise IndexError

    name, old_phone, new_phone = args

    record = book.find_record(name)
    if not record:
        raise KeyError("Contact not found.")

    record.update_phone(old_phone, new_phone)
    return f"Phone for {name} updated: {old_phone} > {new_phone}"


@input_error
def show_phone(args: list, book: AddressBook):
    if not len(args) == 1:
        raise IndexError

    name = args[0]
    record = book.find_record(name)

    if not record:
        raise KeyError("Contact not found")

    if not record.phones:
        return f"{name} has no phone numbers."

    phones = ", ".join(phone.value for phone in record.phones)
    return f"{name}'s phone number(s): {phones}"


@input_error
def show_all(book: AddressBook):
    if not book:
        return "No contacts found."

    return "".join(f"\n{record}" for record in book.values())


@input_error
def add_birthday(args, book):
    name, birthday = args
    record = book.find_record(name)
    if isinstance(record, str):
        return "Contact not found."
    record.add_birthday(birthday)
    return f"Birthday added for {name}."


@input_error
def show_birthday(args, book):
    name = args[0]
    record = book.find_record(name)
    if isinstance(record, str):
        return "Contact not found."
    if not record.birthday:
        return f"No birthday recorded for {name}."
    return f"{name}'s birthday: {record.birthday.value.strftime('%d.%m.%Y')}"


@input_error
def birthdays(_, book):
    upcoming = book.get_upcoming_birthdays()
    if not upcoming:
        return "No birthdays in the upcoming week."
    return "\n".join(
        [f"{item['name']} - {item['congratulation_date']}" for item in upcoming]
    )


def save_data(book, filename="addressbook.pkl"):
    with open(filename, "wb") as f:
        pickle.dump(book, f)


def load_data(filename="addressbook.pkl"):
    try:
        with open(filename, "rb") as f:
            return pickle.load(f)
    except FileNotFoundError:
        return AddressBook()


def main():
    # book = AddressBook()
    book = load_data()
    print("Welcome to the assistant bot!")
    while True:
        user_input = input("Enter a command: ")
        command, *args = parse_input(user_input)

        match (command):
            case "close" | "exit":
                print("Good bye!")
                save_data(book)
                break
            case "hello":
                print("How can I help you?")
            case "add":
                print(add_contact(args, book))
            case "change":
                print(change_contact(args, book))
            case "phone":
                print(show_phone(args, book))
            case "all":
                print(show_all(book))
            case "add-birthday":
                print(add_birthday(args, book))
            case "show-birthday":
                print(show_birthday(args, book))
            case "birthdays":
                print(birthdays(args, book))
            case _:
                print("Invalid command.")


if __name__ == "__main__":
    main()
