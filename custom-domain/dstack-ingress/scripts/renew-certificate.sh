#!/bin/bash
source /opt/app-venv/bin/activate

INITIAL=false
while getopts "n" opt; do
    case $opt in
    n)
        INITIAL=true
        ;;
    \?)
        echo "Invalid option: -$OPTARG" >&2
        exit 1
        ;;
    esac
done

# Check if this is initial certificate obtaining or renewal
if [ ! -f "/etc/letsencrypt/live/$DOMAIN/fullchain.pem" ]; then
    echo "Obtaining new certificate for $DOMAIN using ${DNS_PROVIDER:-cloudflare}"
    ACTION="obtain"
else
    echo "Renewing certificate for $DOMAIN using ${DNS_PROVIDER:-cloudflare}"
    ACTION="renew"
fi

# Perform certificate operation based on DNS provider
case "${DNS_PROVIDER:-cloudflare}" in
cloudflare)
    if [ "$ACTION" = "obtain" ]; then
        CERT_OUTPUT=$(certbot certonly --dns-cloudflare --dns-cloudflare-credentials ~/.cloudflare/cloudflare.ini --dns-cloudflare-propagation-seconds 120 --email $CERTBOT_EMAIL --agree-tos --no-eff-email --non-interactive -d $DOMAIN 2>&1)
    else
        CERT_OUTPUT=$(certbot renew --dns-cloudflare --dns-cloudflare-credentials ~/.cloudflare/cloudflare.ini --dns-cloudflare-propagation-seconds 120 --non-interactive 2>&1)
    fi
    CERT_STATUS=$?
    ;;
linode)
    if [ "$ACTION" = "obtain" ]; then
        CERT_OUTPUT=$(certbot certonly --dns-linode --dns-linode-credentials ~/.linode/credentials.ini --dns-linode-propagation-seconds 300 --email $CERTBOT_EMAIL --agree-tos --no-eff-email --non-interactive -d $DOMAIN 2>&1)
    else
        CERT_OUTPUT=$(certbot renew --dns-linode --dns-linode-credentials ~/.linode/credentials.ini --dns-linode-propagation-seconds 300 --non-interactive 2>&1)
    fi
    CERT_STATUS=$?
    ;;
*)
    echo "Error: Unsupported DNS provider for certbot: ${DNS_PROVIDER}"
    exit 1
    ;;
esac

# Check if certificate operation failed
if [ $CERT_STATUS -ne 0 ]; then
    echo "Certificate $ACTION failed" >&2
    echo "$CERT_OUTPUT" >&2
    exit 1
fi

# Check if no renewals were attempted (only for renewal action)
if [ "$INITIAL" = false ] && [ "$ACTION" = "renew" ] && echo "$CERT_OUTPUT" | grep -q "No renewals were attempted"; then
    echo "No certificates need renewal, skipping evidence generation"
    exit 0
fi

# Generate evidences (for both obtain and renew)
echo "Generating evidence files..."
generate-evidences.sh

# Reload Nginx if certificates were obtained/renewed
if [ "$ACTION" = "obtain" ] || [ "$INITIAL" = true ]; then
    echo "Certificate obtained successfully for $DOMAIN"
elif ! nginx -s reload; then
    echo "Nginx reload failed" >&2
    exit 2
else
    echo "Certificate renewed and Nginx reloaded successfully for $DOMAIN"
fi

exit 0
