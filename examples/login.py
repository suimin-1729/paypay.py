from paypaypy import PayPay

PHONE_NUMBER = "09012345678"
PASSWORD = "qwerty1234"

def main():
    paypay = PayPay()

    try:
        paypay.login_start(PHONE_NUMBER, PASSWORD)
    except:
        print("Login Failed")
        return
    
    url = input("URL: ")

    try:
        paypay.login_confirm(url)
    except:
        print("Login Failed")
        return
    
    print("Login Success")

    with open("./token.txt", "w", encoding="utf-8") as file:
        file.write(paypay.access_token)

if __name__ == "__main__":
    main()