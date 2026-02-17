#!/usr/bin/env python3
"""
Seeder - Crea utente admin di default
"""

from app import app
from db import db
from models.user import User
from models.role import Role

def seed_admin():
    """Crea utente admin di default"""
    with app.app_context():
        # Assicurati che i ruoli esistano
        admin_role = Role.query.filter_by(name='admin').first()
        if not admin_role:
            print("❌ Ruolo admin non trovato. Eseguire prima l'inizializzazione del database.")
            return False
        
        # Email admin
        admin_email = 'giorgio.contarini@triboo.it'
        
        # Verifica se l'utente esiste già
        existing_user = User.query.filter_by(email=admin_email).first()
        
        if existing_user:
            # Aggiorna a admin se non lo è già
            if existing_user.role_id != admin_role.id:
                existing_user.role_id = admin_role.id
                existing_user.is_active = True
                db.session.commit()
                print(f"✅ Utente {admin_email} aggiornato a admin")
            else:
                print(f"✅ Utente {admin_email} già esistente come admin")
            return True
        
        # Crea nuovo utente admin
        # Usa un Google ID temporaneo che verrà aggiornato al primo login
        admin_user = User(
            google_id=f'seed_admin_{admin_email.replace("@", "_at_")}',
            email=admin_email,
            name='Giorgio Contarini',
            role_id=admin_role.id,
            is_active=True
        )
        
        try:
            db.session.add(admin_user)
            db.session.commit()
            print(f"✅ Utente admin creato: {admin_email}")
            print(f"   Google ID temporaneo: {admin_user.google_id}")
            print(f"   Ruolo: {admin_user.role.name}")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Errore nella creazione utente admin: {e}")
            return False

if __name__ == '__main__':
    seed_admin()
