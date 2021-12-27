#!/bin/bash
cd "${0%/*}"
source "config.sh"
curl https://members.hacman.org.uk/query2.php?key=${SECRETKEY} -o "members" 

curl --location --request POST 'https://members.hacman.org.uk/acs/node/heartbeat' \
--header "ApiKey: ${MEMBERSYSTEMKEY}"