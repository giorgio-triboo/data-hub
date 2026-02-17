#!/usr/bin/env python3
"""
Service Monitor - Monitora lo stato dei servizi DataHub
"""

import os
import logging
import requests
import psycopg2
import pymysql
from datetime import datetime
from typing import Dict

logger = logging.getLogger(__name__)


class ServiceMonitor:
    """Monitora lo stato dei servizi DataHub"""
    
    def __init__(self):
        # PostgreSQL configuration (shared instance)
        self.postgres_host = os.getenv('POSTGRES_HOST', 'postgres')
        self.postgres_port = int(os.getenv('POSTGRES_PORT', 5432))
        self.postgres_user = os.getenv('POSTGRES_USER', 'wrapper_user')
        self.postgres_password = os.getenv('POSTGRES_PASSWORD', 'wrapper_pass')
        self.postgres_db = os.getenv('POSTGRES_DB', 'wrapper_config')
        
        # MySQL configuration
        self.mysql_host = os.getenv('MYSQL_HOST', 'mysql')
        self.mysql_port = int(os.getenv('MYSQL_PORT', 3306))
        self.mysql_user = os.getenv('MYSQL_USER', 'datahub_user')
        self.mysql_password = os.getenv('MYSQL_PASSWORD', 'mysql_pass')
        self.mysql_database = os.getenv('MYSQL_DATABASE', 'datahub_crud')
        
        # ClickHouse configuration
        self.clickhouse_host = os.getenv('CLICKHOUSE_HOST', 'clickhouse')
        self.clickhouse_port = int(os.getenv('CLICKHOUSE_PORT', 8123))
        self.clickhouse_user = os.getenv('CLICKHOUSE_USER', 'default')
        self.clickhouse_password = os.getenv('CLICKHOUSE_PASSWORD', '')
        self.clickhouse_db = os.getenv('CLICKHOUSE_DB', 'marketing_data')
        
        # Metabase configuration
        self.metabase_url = os.getenv('METABASE_URL', 'http://metabase:3000')
        
        # Wrapper configuration
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '60'))
    
    def check_postgres(self) -> Dict[str, any]:
        """Verifica connessione PostgreSQL (database wrapper_config)"""
        try:
            conn = psycopg2.connect(
                host=self.postgres_host,
                port=self.postgres_port,
                user=self.postgres_user,
                password=self.postgres_password,
                database=self.postgres_db,
                connect_timeout=5
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return {'status': 'healthy', 'message': 'PostgreSQL connection OK'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'PostgreSQL error: {str(e)}'}
    
    def check_mysql(self) -> Dict[str, any]:
        """Verifica connessione MySQL"""
        try:
            conn = pymysql.connect(
                host=self.mysql_host,
                port=self.mysql_port,
                user=self.mysql_user,
                password=self.mysql_password,
                database=self.mysql_database,
                connect_timeout=5
            )
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            cursor.close()
            conn.close()
            return {'status': 'healthy', 'message': 'MySQL connection OK'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'MySQL error: {str(e)}'}
    
    def check_clickhouse(self) -> Dict[str, any]:
        """Verifica healthcheck ClickHouse"""
        try:
            response = requests.get(
                f'http://{self.clickhouse_host}:{self.clickhouse_port}/ping',
                timeout=10
            )
            if response.status_code == 200 and response.text.strip() == 'Ok':
                return {'status': 'healthy', 'message': 'ClickHouse OK'}
            else:
                return {'status': 'unhealthy', 'message': f'Status code: {response.status_code}'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'ClickHouse error: {str(e)}'}
    
    def check_metabase(self) -> Dict[str, any]:
        """Verifica healthcheck Metabase"""
        try:
            # Metabase è sulla porta 3000 internamente nel container
            # ma potrebbe non essere ancora avviato o non raggiungibile
            response = requests.get(
                f'{self.metabase_url}/api/health',
                timeout=5
            )
            if response.status_code == 200:
                return {'status': 'healthy', 'message': 'Metabase OK'}
            else:
                return {'status': 'unhealthy', 'message': f'Status code: {response.status_code}'}
        except requests.exceptions.ConnectionError as e:
            # Connection refused significa che Metabase non è ancora avviato o non raggiungibile
            return {'status': 'unhealthy', 'message': f'Metabase non raggiungibile (porta 3000). Verifica che il servizio sia avviato.'}
        except Exception as e:
            return {'status': 'unhealthy', 'message': f'Metabase error: {str(e)}'}
    
    def get_all_services_status(self, airbyte_status: Dict = None) -> Dict[str, Dict[str, any]]:
        """Ottiene lo stato di tutti i servizi"""
        services = {
            'PostgreSQL': self.check_postgres(),
            'MySQL': self.check_mysql(),
            'ClickHouse': self.check_clickhouse(),
            'Metabase': self.check_metabase()
        }
        
        # Aggiungi Airbyte se disponibile
        if airbyte_status and airbyte_status.get('status') != 'disabled':
            services['Airbyte'] = airbyte_status
        
        return services
    
    def run_healthcheck(self, airbyte_status: Dict = None):
        """Esegue healthcheck su tutti i servizi"""
        logger.info("=" * 70)
        logger.info(f"Starting healthcheck cycle - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info("=" * 70)
        
        services = self.get_all_services_status(airbyte_status)
        
        all_healthy = True
        healthy_count = 0
        unhealthy_count = 0
        unhealthy_services = []
        
        for service_name, result in services.items():
            status = result['status']
            message = result['message']
            
            if status == 'healthy':
                logger.info(f"✓ {service_name:20s}: {message}")
                healthy_count += 1
            elif status == 'disabled':
                logger.info(f"○ {service_name:20s}: {message} (not configured)")
            else:
                logger.error(f"✗ {service_name:20s}: {message}")
                unhealthy_count += 1
                unhealthy_services.append(service_name)
                all_healthy = False
        
        logger.info("-" * 70)
        logger.info(f"Summary: {healthy_count} healthy, {unhealthy_count} unhealthy")
        logger.info(f"All services healthy: {all_healthy}")
        logger.info("=" * 70)
        
        # Invia alert email se ci sono servizi unhealthy
        if unhealthy_services:
            self.send_alert_email(unhealthy_services, services)
        
        return all_healthy
    
    def send_alert_email(self, unhealthy_services: list, all_services: Dict):
        """Invia alert email quando servizi sono down"""
        try:
            smtp_enabled = os.getenv('SMTP_ENABLED', 'false').lower() == 'true'
            if not smtp_enabled:
                return
            
            import smtplib
            from email.mime.text import MIMEText
            from email.mime.multipart import MIMEMultipart
            
            smtp_host = os.getenv('SMTP_HOST', 'smtp.gmail.com')
            smtp_port = int(os.getenv('SMTP_PORT', '587'))
            smtp_user = os.getenv('SMTP_USER', '')
            smtp_password = os.getenv('SMTP_PASSWORD', '')
            alert_email = os.getenv('ALERT_EMAIL', '')
            
            if not smtp_user or not smtp_password or not alert_email:
                logger.warning("Email alert configured but credentials missing")
                return
            
            # Costruisci messaggio
            msg = MIMEMultipart()
            msg['From'] = smtp_user
            msg['To'] = alert_email
            msg['Subject'] = f'🚨 DataHub Alert: {len(unhealthy_services)} Service(s) Down'
            
            body = f"""
DataHub Service Alert

The following service(s) are currently unhealthy:

"""
            for service_name in unhealthy_services:
                service_status = all_services.get(service_name, {})
                body += f"  ✗ {service_name}: {service_status.get('message', 'Unknown error')}\n"
            
            body += f"""

Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Dashboard: http://localhost:18080

Please check the service status and logs.
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Invia email
            server = smtplib.SMTP(smtp_host, smtp_port)
            server.starttls()
            server.login(smtp_user, smtp_password)
            server.send_message(msg)
            server.quit()
            
            logger.info(f"Alert email sent to {alert_email} for {len(unhealthy_services)} unhealthy service(s)")
        except Exception as e:
            logger.error(f"Error sending alert email: {e}", exc_info=True)
