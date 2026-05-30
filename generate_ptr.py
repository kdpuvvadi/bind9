#!/usr/bin/env python3
import datetime
import os
import sys
from collections import defaultdict

try:
    import dns.zone
    from dns.rdatatype import A
except ImportError:
    print("Error: 'dnspython' is required. Run: pip install dnspython")
    sys.exit(1)

# --- REPO CONFIGURATION ---
CONFIG_DIR = "./config"
REVERSE_CONF_NAME = "named.conf.reverse"

PRIMARY_NS = "ns.dns.puvvadi.net."
ADMIN_EMAIL = "info.puvvadi.net."
TODAY_SERIAL = datetime.datetime.now().strftime("%Y%m%d01")


def parse_all_zones():
    reverse_map = defaultdict(list)

    if not os.path.exists(CONFIG_DIR):
        print(f"ERROR: Base configuration directory '{CONFIG_DIR}' not found.")
        sys.exit(1)

    zone_files = [f for f in os.listdir(CONFIG_DIR) if f.endswith(".zone")]

    for zone_file in zone_files:
        file_path = os.path.join(CONFIG_DIR, zone_file)
        try:
            # Manually extract the $ORIGIN to pass to dnspython as an anchor point
            with open(file_path, "r") as f:
                origin = None
                for line in f:
                    if line.strip().startswith("$ORIGIN"):
                        origin = line.split()[1]
                        if not origin.endswith("."):
                            origin += "."
                        break

            if not origin:
                continue

            zone = dns.zone.from_file(file_path, origin=origin)
            print(f"Parsing Forward Zone: {zone_file} -> Origin: {origin}")

            for name, node in zone.nodes.items():
                name_str = str(name)

                # Exclude wildcard records from generating reverse PTR lines
                if name_str.startswith("*"):
                    continue

                # Process FQDN calculations completely
                if name_str == "@":
                    fqdn = origin
                else:
                    fqdn = f"{name_str}.{origin}"

                # CRITICAL FIX: Ensure an absolute trailing dot is present
                if not fqdn.endswith("."):
                    fqdn += "."

                for rdataset in node.rdatasets:
                    if rdataset.rdtype == A:
                        for rdata in rdataset:
                            ip = rdata.address
                            parts = ip.split(".")
                            if len(parts) == 4:
                                subnet = ".".join(parts[:3])
                                last_octet = parts[3]

                                # Deduplicate records by checking if tuple exists
                                record_tuple = (int(last_octet), fqdn)
                                if record_tuple not in reverse_map[subnet]:
                                    reverse_map[subnet].append(record_tuple)

        except Exception as e:
            print(f"Failed parsing file {zone_file}: {e}")

    return reverse_map


def write_reverse_zones_and_config(reverse_map):
    named_conf_entries = []

    for subnet, records in reverse_map.items():
        seen_octets = set()
        unique_records = []

        # Sort predictably (lowest host octet address first)
        records.sort(key=lambda x: (x[0], x[1]))

        # Prioritize the first unique forward name found per IP address host octet
        for last_octet, fqdn in records:
            if last_octet not in seen_octets:
                seen_octets.add(last_octet)
                unique_records.append((last_octet, fqdn))

        # FIX: Correctly reverse the network octets for in-addr.arpa string naming
        subnet_parts = subnet.split(".")
        reverse_zone_name = (
            f"{subnet_parts[2]}.{subnet_parts[1]}.{subnet_parts[0]}.in-addr.arpa"
        )
        file_name = f"db.{subnet}.reverse"
        output_path = os.path.join(CONFIG_DIR, file_name)

        print(f"Writing Cleaned Reverse Zone File -> {output_path}")

        with open(output_path, "w") as f:
            f.write(f"$ORIGIN {reverse_zone_name}.\n")
            f.write(f"$TTL 86400\n")
            f.write(f"@               IN      SOA     {PRIMARY_NS} {ADMIN_EMAIL} (\n")
            f.write(f"                                {TODAY_SERIAL} ; Serial\n")
            f.write(f"                                3600       ; Refresh\n")
            f.write(f"                                3600       ; Retry\n")
            f.write(f"                                2419200    ; Expire\n")
            f.write(f"                                3600       ; Minimum TTL\n")
            f.write(f"                                )\n\n")
            f.write(f"                IN      NS      {PRIMARY_NS}\n\n")

            for last_octet, fqdn in unique_records:
                # Format output records with precise absolute dot endings
                f.write(f"{last_octet:<15} IN      PTR     {fqdn}\n")

        conf_snippet = (
            f'zone "{reverse_zone_name}" IN {{\n'
            f"  type master;\n"
            f'  file "/etc/bind/{file_name}";\n'
            f"}};"
        )
        named_conf_entries.append(conf_snippet)

    # Save out the master include config structural layout
    reverse_conf_path = os.path.join(CONFIG_DIR, REVERSE_CONF_NAME)
    with open(reverse_conf_path, "w") as f:
        f.write(
            f"// Autogenerated on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        for entry in named_conf_entries:
            f.write(entry + "\n\n")

    print("\nAll reverse mappings are strictly absolute and synchronized.")


if __name__ == "__main__":
    records = parse_all_zones()
    if records:
        write_reverse_zones_and_config(records)
