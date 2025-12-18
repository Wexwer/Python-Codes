import re

# text = """
# Hello John, please email me at john.doe@example.com.
# Also, contact support at support@mycompany.org for assistance.
# Thank you!
# """

user_input = input("Please enter the text: ")

email_pattern = r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+[a-zA-Z]{2,}"

email_redacted = re.sub(email_pattern, "Email Redacted", user_input)

print(email_redacted)