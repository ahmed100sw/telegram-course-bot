import aiosqlite
import config
from datetime import datetime, timedelta
import secrets


class Database:
    def __init__(self):
        self.db_path = config.DATABASE_PATH

    async def init_db(self):
        """Initialize database with all required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            # Users table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    first_name TEXT,
                    is_admin INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Courses table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS courses (
                    course_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT,
                    price REAL DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            # Episodes table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS episodes (
                    episode_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    course_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT,
                    video_path TEXT NOT NULL,
                    price REAL NOT NULL,
                    episode_number INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (course_id) REFERENCES courses (course_id)
                )
            ''')

            # Purchases table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS purchases (
                    purchase_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    episode_id INTEGER NOT NULL,
                    purchased_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    payment_status TEXT DEFAULT 'pending',
                    receipt_photo TEXT,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (episode_id) REFERENCES episodes (episode_id),
                    UNIQUE(user_id, episode_id)
                )
            ''')

            # Video tokens table
            await db.execute('''
                CREATE TABLE IF NOT EXISTS video_tokens (
                    token TEXT PRIMARY KEY,
                    user_id INTEGER NOT NULL,
                    episode_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id),
                    FOREIGN KEY (episode_id) REFERENCES episodes (episode_id)
                )
            ''')

            await db.commit()

    # User methods
    async def add_user(self, user_id: int, username: str = None, first_name: str = None):
        """Add or update user in database"""
        async with aiosqlite.connect(self.db_path) as db:
            is_admin = 1 if user_id == config.ADMIN_ID else 0
            await db.execute('''
                INSERT OR REPLACE INTO users (user_id, username, first_name, is_admin)
                VALUES (?, ?, ?, ?)
            ''', (user_id, username, first_name, is_admin))
            await db.commit()

    async def is_admin(self, user_id: int) -> bool:
        """Check if user is admin"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT is_admin FROM users WHERE user_id = ?', (user_id,)) as cursor:
                result = await cursor.fetchone()
                return result[0] == 1 if result else False

    async def get_all_users(self):
        """Get all users"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT user_id, username, first_name, is_admin, created_at FROM users') as cursor:
                return await cursor.fetchall()

    # Course methods
    async def add_course(self, title: str, description: str = None, price: float = 0):
        """Add a new course"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO courses (title, description, price)
                VALUES (?, ?, ?)
            ''', (title, description, price))
            await db.commit()
            return cursor.lastrowid

    async def get_all_courses(self):
        """Get all courses"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT course_id, title, description, price FROM courses ORDER BY course_id') as cursor:
                return await cursor.fetchall()

    async def get_course(self, course_id: int):
        """Get course by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('SELECT course_id, title, description, price FROM courses WHERE course_id = ?', (course_id,)) as cursor:
                return await cursor.fetchone()

    async def delete_course(self, course_id: int):
        """Delete a course and its episodes"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM episodes WHERE course_id = ?', (course_id,))
            await db.execute('DELETE FROM courses WHERE course_id = ?', (course_id,))
            await db.commit()

    # Episode methods
    async def add_episode(self, course_id: int, title: str, description: str, video_path: str, price: float, episode_number: int):
        """Add a new episode"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute('''
                INSERT INTO episodes (course_id, title, description, video_path, price, episode_number)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (course_id, title, description, video_path, price, episode_number))
            await db.commit()
            return cursor.lastrowid

    async def get_course_episodes(self, course_id: int):
        """Get all episodes for a course"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT episode_id, title, description, price, episode_number
                FROM episodes
                WHERE course_id = ?
                ORDER BY episode_number
            ''', (course_id,)) as cursor:
                return await cursor.fetchall()

    async def get_episode(self, episode_id: int):
        """Get episode by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT episode_id, course_id, title, description, video_path, price, episode_number
                FROM episodes
                WHERE episode_id = ?
            ''', (episode_id,)) as cursor:
                return await cursor.fetchone()

    async def delete_episode(self, episode_id: int):
        """Delete an episode"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('DELETE FROM episodes WHERE episode_id = ?', (episode_id,))
            await db.commit()

    # Purchase methods
    async def create_purchase(self, user_id: int, episode_id: int, receipt_photo: str):
        """Create a new purchase request"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute('''
                    INSERT INTO purchases (user_id, episode_id, receipt_photo, payment_status)
                    VALUES (?, ?, ?, 'pending')
                ''', (user_id, episode_id, receipt_photo))
                await db.commit()
                return True
            except aiosqlite.IntegrityError:
                return False  # Already purchased

    async def get_pending_purchases(self):
        """Get all pending purchase requests"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT p.purchase_id, p.user_id, p.episode_id, p.receipt_photo, 
                       u.username, e.title, e.price
                FROM purchases p
                JOIN users u ON p.user_id = u.user_id
                JOIN episodes e ON p.episode_id = e.episode_id
                WHERE p.payment_status = 'pending'
                ORDER BY p.purchased_at DESC
            ''') as cursor:
                return await cursor.fetchall()

    async def approve_purchase(self, purchase_id: int):
        """Approve a purchase"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE purchases
                SET payment_status = 'approved'
                WHERE purchase_id = ?
            ''', (purchase_id,))
            await db.commit()

    async def reject_purchase(self, purchase_id: int):
        """Reject a purchase"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                UPDATE purchases
                SET payment_status = 'rejected'
                WHERE purchase_id = ?
            ''', (purchase_id,))
            await db.commit()

    async def get_purchase(self, purchase_id: int):
        """Get purchase by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT purchase_id, user_id, episode_id, payment_status
                FROM purchases
                WHERE purchase_id = ?
            ''', (purchase_id,)) as cursor:
                return await cursor.fetchone()

    async def get_user_purchases(self, user_id: int):
        """Get all approved purchases for a user"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT e.episode_id, e.title, c.title as course_title, e.episode_number
                FROM purchases p
                JOIN episodes e ON p.episode_id = e.episode_id
                JOIN courses c ON e.course_id = c.course_id
                WHERE p.user_id = ? AND p.payment_status = 'approved'
                ORDER BY c.course_id, e.episode_number
            ''', (user_id,)) as cursor:
                return await cursor.fetchall()

    async def has_access(self, user_id: int, episode_id: int) -> bool:
        """Check if user has access to an episode"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT COUNT(*) FROM purchases
                WHERE user_id = ? AND episode_id = ? AND payment_status = 'approved'
            ''', (user_id, episode_id)) as cursor:
                result = await cursor.fetchone()
                return result[0] > 0

    # Token methods
    async def create_video_token(self, user_id: int, episode_id: int) -> str:
        """Create a video access token"""
        token = secrets.token_urlsafe(32)
        expires_at = datetime.now() + timedelta(hours=config.TOKEN_EXPIRY_HOURS)
        
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute('''
                INSERT INTO video_tokens (token, user_id, episode_id, expires_at)
                VALUES (?, ?, ?, ?)
            ''', (token, user_id, episode_id, expires_at.isoformat()))
            await db.commit()
        
        return token

    async def validate_token(self, token: str):
        """Validate a video token and return episode info"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute('''
                SELECT vt.user_id, vt.episode_id, vt.expires_at, e.video_path, e.title
                FROM video_tokens vt
                JOIN episodes e ON vt.episode_id = e.episode_id
                WHERE vt.token = ?
            ''', (token,)) as cursor:
                result = await cursor.fetchone()
                
                if not result:
                    return None
                
                user_id, episode_id, expires_at, video_path, title = result
                
                # Check if token is expired
                if datetime.fromisoformat(expires_at) < datetime.now():
                    return None
                
                return {
                    'user_id': user_id,
                    'episode_id': episode_id,
                    'video_path': video_path,
                    'title': title
                }

    async def get_stats(self):
        """Get bot statistics"""
        async with aiosqlite.connect(self.db_path) as db:
            # Total users
            async with db.execute('SELECT COUNT(*) FROM users') as cursor:
                total_users = (await cursor.fetchone())[0]
            
            # Total courses
            async with db.execute('SELECT COUNT(*) FROM courses') as cursor:
                total_courses = (await cursor.fetchone())[0]
            
            # Total episodes
            async with db.execute('SELECT COUNT(*) FROM episodes') as cursor:
                total_episodes = (await cursor.fetchone())[0]
            
            # Total sales
            async with db.execute('SELECT COUNT(*) FROM purchases WHERE payment_status = "approved"') as cursor:
                total_sales = (await cursor.fetchone())[0]
            
            # Pending purchases
            async with db.execute('SELECT COUNT(*) FROM purchases WHERE payment_status = "pending"') as cursor:
                pending_purchases = (await cursor.fetchone())[0]
            
            # Total revenue
            async with db.execute('''
                SELECT SUM(e.price)
                FROM purchases p
                JOIN episodes e ON p.episode_id = e.episode_id
                WHERE p.payment_status = 'approved'
            ''') as cursor:
                total_revenue = (await cursor.fetchone())[0] or 0
            
            return {
                'total_users': total_users,
                'total_courses': total_courses,
                'total_episodes': total_episodes,
                'total_sales': total_sales,
                'pending_purchases': pending_purchases,
                'total_revenue': total_revenue
            }


# Global database instance
db = Database()
