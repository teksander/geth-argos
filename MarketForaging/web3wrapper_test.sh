
echo "+-----------------------------------------------------------+"
echo "Waiting web3 to respond..."

ready=0
    for host in $(awk '{print $4}' identifiers.txt); do
        if echo -e '\x1dclose\x0d' | telnet $host 4000 2>/dev/null | grep -q Connected ; then
            let "ready=ready+1"
            echo "$host responded"
        fi
    done
    echo "Total responded: $ready"