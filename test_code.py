def bad_function():
    global counter
    counter = 0
    
    while True:
        counter += 1
        if counter > 1000:
            break
    
    file = open("data.txt", "r")
    content = file.read()
    # Missing file.close()
    
    query = f"SELECT * FROM users WHERE id = {user_id}"
    cursor.execute(query)
    
    password = "hardcoded_password_123"
    api_key = "sk-1234567890abcdef"
    
    return content 