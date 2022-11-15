# importing string so ASCII can concatenate lowercase and uppercase letters
from genericpath import exists
import string
# importing random to gain access to the random module
import random

# creating variables to store list conversions used to generate password
alphabet = list(string.ascii_letters)
digits = list(string.digits)
special_characters = list("!@#$%^&*()")
characters = alphabet + digits + special_characters
# print(characters) - uncomment to check string output

def password_generator():
    # defining the user password length
    length = int(input("Enter password length: "))

    # defining the character count for each variable
    alphabet_count = int(input("Enter alphabet count for password: "))
    digits_count = int(input("Enter numeric count for password: "))
    special_characters_count = int(input("Enter special character count for password: "))

    characters_count = alphabet_count + digits_count + special_characters_count

    # Next is to check the total length of characters with a sum count
    # Print invalid if the sum is greater than the length

    if characters_count > length:
        print("Characters total count is greater than the defined password length ")
        return

    # a list to store the created password in
    created_password = []

    # picking random alphabets
    for i in range(alphabet_count):
        created_password.append(random.choice(alphabet))

    # picking random digits
    for i in range(digits_count):
        created_password.append(random.choice(digits))

    # picking random special characters
    for i in range(special_characters_count):
        created_password.append(random.choice(special_characters))

    ## if character count is < than password length, random characters will be added to the password to make it equal
    ##  to the defined password length
    if characters_count < length:
        random.shuffle(characters)
        for i in range(length - characters_count):
            created_password.append(random.choice(characters))

    # option to shuffle the password to add another random element to it
    random.shuffle(created_password)

    # password list must now be converted back to a string
    print("".join(created_password))

    return(created_password)

# Call the function

password_generated = str(password_generator())

password_storage = []

for password in password_generated():
    if password in password_generated():
        password_storage += password
    break
        
    


password_generator()

print(password_storage)






