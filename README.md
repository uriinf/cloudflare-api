# CloudFlare purge cache with API

## ansible-cf-purge-cache.yml is ansible ad-hoc to purge all files in zone
Just replace 3 variables cloudflare_purge_email, cloudflare_purge_key, cloudflare_purge_zone and run:
```bash
ansible-playbook ansible-cf-purge-cache.yml
```

## cf-purge-list.py
Purge individual files for all A records of zone.
```bash
./cf-purge-list.py --cf-api-key 0000000000000000000000000 --cf-api-email myemail@example.com -d mycloudflaredomain.com -s static.list
```
* Required parameters:
 * -d - CloudFlare zone to clean cache
 * -s - path to file with list of objects should be purged
 * --cf-api-key - CloudFlare API Key, could be taken from system environment CF_API_KEY
 * --cf-api-email - CloudFlare API email, , could be taken from system environment CF_EMAIL_KEY

# Useful links:
https://api.cloudflare.com/  
https://github.com/cloudflare/python-cloudflare
