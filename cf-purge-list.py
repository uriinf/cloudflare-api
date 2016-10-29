#!/usr/bin/env python3
import sys
import os
import argparse
import urllib.request
import json
import datetime


# Define functions
def cloudflare_request(request_path, request_method):
    req = urllib.request.Request(cloudflare_baseurl + request_path, method=request_method)
    req.add_header('X-Auth-Email', auth_email)
    req.add_header('X-Auth-Key', auth_key)
    req.add_header('Content-Type', 'application/json')

    try:
        f = urllib.request.urlopen(req)
    except urllib.error.URLError as e:
        print(e.reason, e.code)
        exit_state = 3
        exit(exit_state)

    json_obj = json.loads(f.read().decode('utf-8'))
    return json_obj


def cloudflare_purge_file(request_path, batch_item):
    request_data = '{ "files" : ' + json.dumps(batch_item) + '}'
    data_bytes = request_data.encode('utf8')
    req = urllib.request.Request(cloudflare_baseurl + request_path, method='DELETE', data=data_bytes)
    req.add_header('X-Auth-Email', auth_email)
    req.add_header('X-Auth-Key', auth_key)
    req.add_header('Content-Type', 'application/json')

    try:
        f = urllib.request.urlopen(req, )
    except urllib.error.URLError as e:
        return (e.reason + ' code: ' + str(e.code))

    json_obj = json.loads(f.read().decode('utf-8'))
    return json_obj


def gen_batches(domains_list, objects_list, batch_size):
    batch_list = []
    multi_list = []
    for domain_id in domains_list:
        for purge_object in objects_list:
            if len(batch_list) >= batch_size:
                multi_list.append(batch_list)
                batch_list = []
                batch_list.append('http://' + domain_id + purge_object)
                batch_list.append('https://' + domain_id + purge_object)
            else:
                batch_list.append('http://' + domain_id + purge_object)
                batch_list.append('https://' + domain_id + purge_object)
    multi_list.append(batch_list)
    return multi_list


def gen_static_list(rsync_output_file):
    try:
        f = open(rsync_output_file, 'r')
    except Exception as e:
        print('\nCant open open file: ', rsync_output_file)
        exit(3)
    if not args.quiet:
        print ('Raw rsync list size: ', len(rsync_output_file))
    raw_list = json.loads(f.read())
    normalized_list = ['/' + item.replace('deleting ', '') for item in raw_list if not item.endswith('/')]
    if not args.quiet:
        print ('Normalized rsync list size: ', len(normalized_list))
    return normalized_list


def write_failed(outfile, out_list):
    try:
        f = open(outfile, 'w')
    except Exception as e:
        print('\nCant open open file or file not writable: ', outfile)
        exit(2)
    json.dump(out_list, f)
    f.close()

# Define variables
cloudflare_baseurl = 'https://api.cloudflare.com/client/v4'
records_name_list = []
record_type = 'A'
purge_list = []
unsuccess_list = []

# Args: CloudFlare auth parameters
parser = argparse.ArgumentParser(description='CloudFlare purge cache by URL, https://api.cloudflare.com/#zone-purge-individual-files-by-url-and-cache-tags')
parser.add_argument('--cf-api-email', help='CloudFlare account email, could be defined with system env: export CF_API_EMAIL=user@example.com')
parser.add_argument('--cf-api-key', help='CloudFlare account key, could be defined with system env: export CF_API_KEY=00000000000000000000000000000000')
# Args: Purge parameters
parser.add_argument('--domain', '-d', help='CloudFlare domain', required=True)
parser.add_argument('--rsync-output', '-s', help='Rsync output file', required=True)
parser.add_argument('--batch-size', '-b', help='Array size, default: 4, (max: 30)', type=int, default=4)
parser.add_argument('--output-failed-list', '-o', help='Output file for failed requests')
parser.add_argument('--quiet', '-q', help='Quiet mode', action="store_true")

args = parser.parse_args()

# Define CloudFlare auth parameters
if args.cf_api_email:
    auth_email = args.cf_api_email
elif os.environ.get('CF_API_EMAIL'):
    auth_email = os.environ['CF_API_EMAIL']
else:
    print ('CloudFlare auth parameter auth_email isn\'t defined')
    parser.print_help()
    sys.exit(2)

if args.cf_api_key:
    auth_key = args.cf_api_key
elif os.environ.get('CF_API_KEY'):
    auth_key = os.environ['CF_API_KEY']
else:
    print ('CloudFlare auth parameter auth_key isn\'t defined')
    parser.print_help()
    sys.exit(2)

# open rsync output and create list of updated static files
purge_list = gen_static_list(args.rsync_output)
# Get domain ID
zone_id = cloudflare_request('/zones?name=' + args.domain, 'GET')['result'][0]['id']

# Get DNS records by domain ID
json_obj = cloudflare_request('/zones/' + zone_id + '/dns_records?per_page=100&type=' + record_type, 'GET')
for item in json_obj['result']:
    records_name_list.append(item['name'])
if not args.quiet:
    print ('DNS A records list size: ', len(records_name_list))

batches_list = gen_batches(records_name_list, purge_list, args.batch_size)
if not args.quiet:
    print ('Batch size: %s\nBatches count: %s' % (args.batch_size, len(batches_list)))

# Purge objects
if not args.quiet:
    print ('\nStarting purge requests:', datetime.datetime.now())
for i, item in enumerate(batches_list):
    if not args.quiet:
        print ('\npurging batch #%s: %s' % (i, item))
    purge_result = cloudflare_purge_file('/zones/' + zone_id + '/purge_cache', item)
    if isinstance(purge_result, dict):
        if not purge_result['success']:
            if not args.quiet:
                print ('purging result:', purge_result)
            for item_object in item:
                unsuccess_list.append(item_object)
        else:
            if not args.quiet:
                print ('purging result:', purge_result)
    else:
        if not args.quiet:
            print ('purging result:', purge_result)
        for item_object in item:
            unsuccess_list.append(item_object)

print ('\nPurging finished: %s\nTotal batches processed: %s, objects: %s\nFailed items: %s' % (datetime.datetime.now(), i+1, (i + 1)*args.batch_size, len(unsuccess_list)))
if (len(unsuccess_list) > 0 and args.output_failed_list):
    write_failed(args.output_failed_list, unsuccess_list)
