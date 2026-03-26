from auth import sign_in, sign_up, sign_out

while True:
    action = input("Action: ")
    if(action == "1"):
        email = input("Email: ")
        username = input("Username: ")
        password = input("Password: ") 
        sign_up(email, username, password)
    elif(action == "2"):
        email = input("Email: ")
        password = input("password: ")
        sign_in(email, password)
    elif(action == "3"):
        sign_out()
    else:
        break