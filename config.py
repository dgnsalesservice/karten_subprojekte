# -*- coding: utf-8 -*-
"""
Created on Tue May  6 17:07:26 2025

@author: AnnaMeierDeutscheGig
"""

# config.py – enthält die Zugangsdaten zur PostgreSQL-Datenbank

DB_PARAMS = {
    "host": "pgeuwgispr002.postgres.database.azure.com",         # z. B. 'localhost' oder die IP des DB-Servers
    "port": 5432,                # Standardport PostgreSQL
    "database": "dgn_gis",     # Name deiner Datenbank
    "user": "dgn_data_sales",          # DB-Benutzername
    "password": "xdMi9hJrtmw7KWsnVGX."    # Passwort (Achtung bei Teamsicherheit!)
}

