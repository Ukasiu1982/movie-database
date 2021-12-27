import smtplib

EMAIL_FROM = ''
EMAIL_FROM_PASS = ''
EMAIL_TO = ''


#  dla konta google trzeba wylaczyc zabezpiecznie dostepu dla mniej bezpiecznej aplikacji
def send_email(provider, title):
    email_user = EMAIL_FROM
    server = smtplib.SMTP('smtp.gmail.com', 587)
    server.starttls()
    server.login(email_user, EMAIL_FROM_PASS)

    message = f"{title} jest dostepne w serwisie: {provider['name']}"
    server.sendmail(EMAIL_FROM, EMAIL_TO, message)
    print('email to: ', EMAIL_TO)
    print('message: ', message)
    server.quit()
