Changelog
All notable changes to this project will be documented in this file.
The format is based on Keep a Changelog,
and this project adheres to Semantic Versioning.

[0.4.3] - 2025-06-22 
- Migrated to SQL database
- Added endpoints module archictecture for FastAPI

[0.4.2] - 2025-06-20
- Removed (almost) all references to Firebase storage
- Consolidated logic in fewer, more robust classes
- Deleted redunandat modules

[0.4.1] - 2025-06-19 
- Error handling for duplicate SQL entries
[0.4.0] - 2025-06-18
- Moved backend storage to SQL (Supabase)
- Reworked backend flow to account for database 
- Legacy code still in place

[0.3.2] - 2025-06-13 
- Added StorageService class
- Preparing database migration to PostgreSQL (Supabase)

[0.3.1] - 2025-06-08
- Latest .xlsx upload auto-reads the json file with default times (20:00–22:59)
- Refactored API logic

[0.3.0] - 2025-05-31
- Added ability to read multiple channels, based on dynamic input
- Refactored internal logic

[0.2.0] - 2025-05-29 
- Added ability to read ratings from any timeframe and display it as a table (update from v0.1.2)

[0.1.3] - 2025-05-25 
- Refactored code and hierarchy, improved type hinting, opening the door to code expansion

[0.1.2] - 2025-05-22 
- Added functionality to read ratings from any date, in the 8PM-23PM timeframe
- Improved internal data parsing logic (Modular approach incoming)

[0.1.1] - 2025-05-17 
- Fixed reading from Firebase storage 

[0.1.0] - 2025-05-17 
- First release of the project
