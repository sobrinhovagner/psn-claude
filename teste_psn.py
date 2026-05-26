from psnawp_api import PSNAWP

psnawp = PSNAWP("SE5h7Snvz0YrP3lExxoelA8A8RPGUmeMdqXwZoLC8aUbZOdBUPRQ3CCj4MRFwkoP")
client = psnawp.me()

print("PSN ID:", client.online_id)
print("Conta criada:", client.account_devices)