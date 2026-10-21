# Contracts

Applications remain ordinary native programs. An AppOS manifest declares an app identifier, launch command and requested capabilities; declaration does **not** grant rights. Runtime policy decides what is allowed and must enforce it outside the application process.

`app.example.json` is a proposed starting format, **not an implemented schema**. Any stable contract should have validation, versioning and a minimal developer reference.
