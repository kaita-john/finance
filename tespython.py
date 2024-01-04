def transform_phone_number(phone_number):
    phonenumber = str(phone_number)
    print(f"Trying ", phonenumber)
    if not phonenumber:
        return phonenumber
    if phonenumber == "":
        return phonenumber
    if phonenumber.startswith('0'):
        print("It starts with zero")
        return '254' + phonenumber[1:]
    elif phonenumber.startswith('+254'):
        return phonenumber[1:]
    else:
        return phonenumber





# import base64
#
# file_path = "C:\\Users\\kaita\\OneDrive\\Desktop\\coatOfArms.png"
#
# with open(file_path, "rb") as file:
#     encoded_content = base64.b64encode(file.read()).decode("utf-8")
#
# print(encoded_content)


dated = "12/10/2023"
date_of_admission = str(dated)
print(date_of_admission)