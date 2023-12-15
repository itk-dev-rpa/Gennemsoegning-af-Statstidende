# Gennemsøgning af Statstidende

This robot fetches the newest data from Statstidende.dk and OPUS SAP and checks if any Statstidende cases could be of relevance.

## How to use certificate

Statstidende.dk's API uses a certificate for validation.
The robot stores the certificate in a AES encrypted version.

If you have a .p12 certificate file use the following command to convert it to a .pem file:

```bash
openssl pkcs12 -in Statstidende_API.p12 -out Certificate.pem -nodes
```