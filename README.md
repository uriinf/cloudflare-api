# CloudFlare purge cache scripts with API

### ansible-cf-purge-cache.yml is ansible ad-hoc to purge all files in zone
Just replace 3 variables cloudflare_purge_email, cloudflare_purge_key, cloudflare_purge_zone and run:
```bash
ansible-playbook ansible-cf-purge-cache.yml
```

# Usefull links:
https://api.cloudflare.com/  
https://github.com/cloudflare/python-cloudflare
