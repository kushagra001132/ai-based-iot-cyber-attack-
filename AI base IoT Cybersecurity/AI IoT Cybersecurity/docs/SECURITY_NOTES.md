# Security Notes

This package is designed for an authorized local lab.

The lab broker intentionally uses:
- allow_anonymous true
- plain MQTT on port 1883
- no TLS

This is convenient for development but not secure for an exposed deployment.

Before real deployment:
1. Bind Mosquitto to a trusted interface or VLAN.
2. Use password authentication.
3. Use topic ACLs.
4. Enable TLS.
5. Rotate credentials.
6. Restrict firewall access.
7. Use persistent device identity.
8. Store logs securely.
9. Protect Grafana/InfluxDB credentials.
10. Keep firmware update mechanisms authenticated.

Do not use the anomaly generator against third-party systems.
