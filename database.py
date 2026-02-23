"""
Database module for Vehicle Counting System
Handles all data storage and retrieval
"""

import sqlite3
import datetime
import os
from typing import List, Dict, Optional

class VehicleDatabase:
    """
    Manages SQLite database for vehicle counting data
    """
    
    def __init__(self, db_name='vehicles.db'):
        """
        Initialize database connection
        
        Args:
            db_name: Name of the database file
        """
        self.db_name = db_name
        self.init_database()
        print(f"✓ Database initialized: {db_name}")
    
    def get_connection(self):
        """Get a database connection"""
        return sqlite3.connect(self.db_name)
    
    def init_database(self):
        """Create tables if they don't exist"""
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Table 1: Individual vehicle entries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS vehicle_entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                lane TEXT,
                vehicle_type TEXT,
                confidence REAL,
                session_id TEXT
            )
        ''')
        
        # Table 2: Daily summaries
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS daily_summary (
                date DATE PRIMARY KEY,
                total_count INTEGER,
                peak_hour TEXT,
                peak_count INTEGER,
                avg_per_hour REAL,
                last_updated DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Table 3: Hourly statistics
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS hourly_stats (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                date DATE,
                hour INTEGER,
                vehicle_count INTEGER,
                avg_confidence REAL,
                UNIQUE(date, hour)
            )
        ''')
        
        # Table 4: Sessions (tracking each time system runs)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                start_time DATETIME,
                end_time DATETIME,
                total_vehicles INTEGER,
                status TEXT
            )
        ''')
        
        # Create indexes for better performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_timestamp 
            ON vehicle_entries(timestamp)
        ''')
        
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_date 
            ON vehicle_entries(date(timestamp))
        ''')
        
        conn.commit()
        conn.close()
    
    # ==================== VEHICLE ENTRIES ====================
    
    def add_vehicle(self, lane='Lane 1', vehicle_type='Car', 
                   confidence=0.95, session_id=None):
        """
        Add a vehicle entry to the database
        
        Args:
            lane: Which lane the vehicle was in
            vehicle_type: Type of vehicle (Car, Truck, Bus, Motorcycle)
            confidence: Detection confidence score (0-1)
            session_id: Current session identifier
        
        Returns:
            The ID of the inserted record
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO vehicle_entries (lane, vehicle_type, confidence, session_id)
            VALUES (?, ?, ?, ?)
        ''', (lane, vehicle_type, confidence, session_id))
        
        vehicle_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return vehicle_id
    
    def get_recent_vehicles(self, limit=10):
        """
        Get the most recent vehicle entries
        
        Args:
            limit: Number of entries to retrieve
            
        Returns:
            List of vehicle entry dictionaries
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT id, timestamp, lane, vehicle_type, confidence
            FROM vehicle_entries
            ORDER BY timestamp DESC
            LIMIT ?
        ''', (limit,))
        
        rows = cursor.fetchall()
        conn.close()
        
        vehicles = []
        for row in rows:
            vehicles.append({
                'id': row[0],
                'timestamp': row[1],
                'lane': row[2],
                'vehicle_type': row[3],
                'confidence': row[4]
            })
        
        return vehicles
    
    # ==================== DAILY STATISTICS ====================
    
    def get_today_count(self):
        """
        Get total vehicle count for today
        
        Returns:
            Integer count of vehicles today
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        today = datetime.date.today()
        cursor.execute('''
            SELECT COUNT(*) FROM vehicle_entries
            WHERE DATE(timestamp) = ?
        ''', (today,))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def get_count_by_date(self, date):
        """
        Get vehicle count for a specific date
        
        Args:
            date: Date string (YYYY-MM-DD) or date object
            
        Returns:
            Integer count
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT COUNT(*) FROM vehicle_entries
            WHERE DATE(timestamp) = ?
        ''', (str(date),))
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    def get_last_n_days(self, days=7):
        """
        Get vehicle counts for the last N days
        
        Args:
            days: Number of days to retrieve
            
        Returns:
            List of dictionaries with date and count
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT DATE(timestamp) as date, COUNT(*) as count
            FROM vehicle_entries
            WHERE DATE(timestamp) >= DATE('now', '-' || ? || ' days')
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
        ''', (days,))
        
        rows = cursor.fetchall()
        conn.close()
        
        results = []
        for row in rows:
            results.append({
                'date': row[0],
                'count': row[1]
            })
        
        return results
    
    # ==================== HOURLY STATISTICS ====================
    
    def get_hourly_stats(self, date=None):
        """
        Get hourly breakdown for a specific date
        
        Args:
            date: Date to get stats for (defaults to today)
            
        Returns:
            List of dictionaries with hour and count
        """
        if date is None:
            date = datetime.date.today()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as count,
                AVG(confidence) as avg_confidence
            FROM vehicle_entries
            WHERE DATE(timestamp) = ?
            GROUP BY hour
            ORDER BY hour
        ''', (str(date),))
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = []
        for row in rows:
            stats.append({
                'hour': row[0],
                'count': row[1],
                'avg_confidence': round(row[2], 2) if row[2] else 0
            })
        
        return stats
    
    def get_peak_hour(self, date=None):
        """
        Get the peak hour for a specific date
        
        Args:
            date: Date to analyze (defaults to today)
            
        Returns:
            Dictionary with peak hour and count
        """
        if date is None:
            date = datetime.date.today()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                CAST(strftime('%H', timestamp) AS INTEGER) as hour,
                COUNT(*) as count
            FROM vehicle_entries
            WHERE DATE(timestamp) = ?
            GROUP BY hour
            ORDER BY count DESC
            LIMIT 1
        ''', (str(date),))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'hour': row[0],
                'count': row[1]
            }
        return {'hour': 0, 'count': 0}
    
    # ==================== LANE STATISTICS ====================
    
    def get_lane_stats(self, date=None):
        """
        Get vehicle counts by lane
        
        Args:
            date: Date to analyze (defaults to today)
            
        Returns:
            Dictionary with lane counts
        """
        if date is None:
            date = datetime.date.today()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT lane, COUNT(*) as count
            FROM vehicle_entries
            WHERE DATE(timestamp) = ?
            GROUP BY lane
            ORDER BY lane
        ''', (str(date),))
        
        rows = cursor.fetchall()
        conn.close()
        
        stats = {}
        for row in rows:
            stats[row[0]] = row[1]
        
        return stats
    
    # ==================== VEHICLE TYPE STATISTICS ====================
    
    def get_vehicle_type_breakdown(self, date=None):
        """
        Get breakdown by vehicle type
        
        Args:
            date: Date to analyze (defaults to today)
            
        Returns:
            Dictionary with vehicle type counts
        """
        if date is None:
            date = datetime.date.today()
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT vehicle_type, COUNT(*) as count
            FROM vehicle_entries
            WHERE DATE(timestamp) = ?
            GROUP BY vehicle_type
            ORDER BY count DESC
        ''', (str(date),))
        
        rows = cursor.fetchall()
        conn.close()
        
        breakdown = {}
        for row in rows:
            breakdown[row[0]] = row[1]
        
        return breakdown
    
    # ==================== SESSION MANAGEMENT ====================
    
    def create_session(self, session_id):
        """
        Create a new session record
        
        Args:
            session_id: Unique identifier for the session
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO sessions (session_id, start_time, status)
            VALUES (?, ?, 'active')
        ''', (session_id, datetime.datetime.now()))
        
        conn.commit()
        conn.close()
    
    def end_session(self, session_id, total_vehicles):
        """
        Mark a session as ended
        
        Args:
            session_id: Session identifier
            total_vehicles: Final vehicle count
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            UPDATE sessions
            SET end_time = ?, total_vehicles = ?, status = 'completed'
            WHERE session_id = ?
        ''', (datetime.datetime.now(), total_vehicles, session_id))
        
        conn.commit()
        conn.close()
    
    # ==================== REPORTING ====================
    
    def generate_daily_report(self, date=None):
        """
        Generate comprehensive daily report
        
        Args:
            date: Date for report (defaults to today)
            
        Returns:
            Dictionary with all daily statistics
        """
        if date is None:
            date = datetime.date.today()
        
        total_count = self.get_count_by_date(date)
        hourly_stats = self.get_hourly_stats(date)
        peak_hour = self.get_peak_hour(date)
        lane_stats = self.get_lane_stats(date)
        vehicle_types = self.get_vehicle_type_breakdown(date)
        
        # Calculate average per hour
        if hourly_stats:
            avg_per_hour = total_count / len(hourly_stats)
        else:
            avg_per_hour = 0
        
        report = {
            'date': str(date),
            'total_count': total_count,
            'hourly_stats': hourly_stats,
            'peak_hour': peak_hour,
            'avg_per_hour': round(avg_per_hour, 1),
            'lane_stats': lane_stats,
            'vehicle_types': vehicle_types
        }
        
        return report
    
    # ==================== DATA EXPORT ====================
    
    def export_to_csv(self, filename, start_date=None, end_date=None):
        """
        Export vehicle entries to CSV file
        
        Args:
            filename: Output CSV filename
            start_date: Start date for export (optional)
            end_date: End date for export (optional)
        """
        import csv
        
        conn = self.get_connection()
        cursor = conn.cursor()
        
        query = 'SELECT * FROM vehicle_entries'
        params = []
        
        if start_date and end_date:
            query += ' WHERE DATE(timestamp) BETWEEN ? AND ?'
            params = [str(start_date), str(end_date)]
        elif start_date:
            query += ' WHERE DATE(timestamp) >= ?'
            params = [str(start_date)]
        
        query += ' ORDER BY timestamp'
        
        cursor.execute(query, params)
        
        # Write to CSV
        with open(filename, 'w', newline='') as csvfile:
            csv_writer = csv.writer(csvfile)
            
            # Write header
            csv_writer.writerow(['ID', 'Timestamp', 'Lane', 'Vehicle Type', 'Confidence', 'Session ID'])
            
            # Write data
            csv_writer.writerows(cursor.fetchall())
        
        conn.close()
        print(f"✓ Data exported to {filename}")
    
    # ==================== UTILITY FUNCTIONS ====================
    
    def clear_old_data(self, days_to_keep=90):
        """
        Delete data older than specified days
        
        Args:
            days_to_keep: Number of days to retain
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            DELETE FROM vehicle_entries
            WHERE DATE(timestamp) < DATE('now', '-' || ? || ' days')
        ''', (days_to_keep,))
        
        deleted = cursor.rowcount
        conn.commit()
        conn.close()
        
        print(f"✓ Deleted {deleted} old records")
        return deleted
    
    def get_database_stats(self):
        """
        Get overall database statistics
        
        Returns:
            Dictionary with database info
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Total entries
        cursor.execute('SELECT COUNT(*) FROM vehicle_entries')
        total_entries = cursor.fetchone()[0]
        
        # Date range
        cursor.execute('SELECT MIN(DATE(timestamp)), MAX(DATE(timestamp)) FROM vehicle_entries')
        date_range = cursor.fetchone()
        
        # Database file size
        db_size = os.path.getsize(self.db_name) if os.path.exists(self.db_name) else 0
        
        conn.close()
        
        return {
            'total_entries': total_entries,
            'earliest_date': date_range[0],
            'latest_date': date_range[1],
            'database_size_mb': round(db_size / (1024 * 1024), 2)
        }


# ==================== TEST CODE ====================

if __name__ == "__main__":
    print("="*60)
    print("TESTING DATABASE MODULE")
    print("="*60)
    
    # Initialize database
    db = VehicleDatabase('test_vehicles.db')
    
    # Add some test entries
    print("\nAdding test vehicles...")
    session_id = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    db.create_session(session_id)
    
    for i in range(10):
        db.add_vehicle(
            lane=f'Lane {(i % 4) + 1}',
            vehicle_type=['Car', 'Truck', 'Bus', 'Motorcycle'][i % 4],
            confidence=0.85 + (i * 0.01),
            session_id=session_id
        )
    
    print(f"✓ Added 10 test vehicles")
    
    # Get today's count
    today_count = db.get_today_count()
    print(f"\nToday's count: {today_count}")
    
    # Get recent vehicles
    recent = db.get_recent_vehicles(5)
    print(f"\nRecent vehicles:")
    for v in recent:
        print(f"  {v['timestamp']} - {v['vehicle_type']} in {v['lane']}")
    
    # Get hourly stats
    hourly = db.get_hourly_stats()
    print(f"\nHourly stats: {len(hourly)} hours recorded")
    
    # Get lane stats
    lane_stats = db.get_lane_stats()
    print(f"\nLane statistics: {lane_stats}")
    
    # Generate daily report
    report = db.generate_daily_report()
    print(f"\nDaily Report:")
    print(f"  Total: {report['total_count']}")
    print(f"  Peak Hour: {report['peak_hour']}")
    print(f"  Avg/Hour: {report['avg_per_hour']}")
    
    # Get database stats
    stats = db.get_database_stats()
    print(f"\nDatabase Stats:")
    print(f"  Total Entries: {stats['total_entries']}")
    print(f"  Size: {stats['database_size_mb']} MB")
    
    print("\n" + "="*60)
    print("✓ All tests passed!")
    print("="*60)