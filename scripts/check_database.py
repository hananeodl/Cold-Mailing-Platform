#!/usr/bin/env python3
"""
Script pour vérifier l'état de la base de données
"""

import os
import sys
from pathlib import Path

project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app import create_app
from app.database import db
from app.models import AccountManager, Customer, Search, Listing, Mailing, Appointment
from sqlalchemy import inspect, text


def check_database():
    """Vérifier l'état de la base de données"""
    app = create_app()

    with app.app_context():
        try:
            print(" VÉRIFICATION DE LA BASE DE DONNÉES")
            print("=" * 60)

            # 1. Tester la connexion
            print("\n1. Test de connexion...")
            db.session.execute(text('SELECT 1'))
            print("  Connexion réussie")

            # 2. Vérifier les tables
            print("\n2. Tables dans la base de données:")
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()

            if not tables:
                print("  Aucune table trouvée!")
                return False

            for table in sorted(tables):
                columns = inspector.get_columns(table)
                print(f"   - {table}: {len(columns)} colonnes")

                # Afficher les 5 premières colonnes
                for col in columns[:5]:
                    print(f"     * {col['name']} ({col['type']})")
                if len(columns) > 5:
                    print(f"     ... et {len(columns) - 5} autres")

            # 3. Compter les enregistrements
            print("\n3. Statistiques des données:")

            models = [
                ('Account Managers', AccountManager),
                ('Customers', Customer),
                ('Searches', Search),
                ('Listings', Listing),
                ('Mailings', Mailing),
                ('Appointments', Appointment)
            ]

            for name, model in models:
                try:
                    count = db.session.query(model).count()
                    print(f"   - {name}: {count}")
                except Exception as e:
                    print(f"   - {name}: ERREUR - {e}")

            # 4. Vérifier les données de test
            print("\n4. Vérification des données de test:")

            # Vérifier l'admin
            admin = AccountManager.query.filter_by(role='ADMIN').first()
            if admin:
                print(f"  Admin trouvé: {admin.first_name} {admin.last_name}")
            else:
                print(" Aucun admin trouvé")

            # Vérifier les customers
            customers = Customer.query.all()
            if customers:
                print(f" {len(customers)} customer(s) trouvé(s)")
                for cust in customers[:3]:  # Afficher les 3 premiers
                    print(f"     - {cust.first_name} {cust.last_name} ({cust.company_name})")
            else:
                print(" Aucun customer trouvé")

            # 5. Vérifier les relations
            print("\n5. Vérification des relations:")

            if customers:
                customer = customers[0]
                print(f"   Customer: {customer.first_name} {customer.last_name}")
                print(f"     - Account Managers: {len(customer.account_managers)}")
                print(f"     - Searches: {len(customer.searches)}")
                print(f"     - Listings: {len(customer.listings)}")

                if customer.listings:
                    listing = customer.listings[0]
                    print(f"     - Mailings pour le premier listing: {len(listing.mailings)}")

            print("\n" + "=" * 60)
            print(" VÉRIFICATION TERMINÉE AVEC SUCCÈS!")

            return True

        except Exception as e:
            print(f"\n ERREUR lors de la vérification: {e}")
            import traceback
            traceback.print_exc()
            return False


if __name__ == '__main__':
    check_database()