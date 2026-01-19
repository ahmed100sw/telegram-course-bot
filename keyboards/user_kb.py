from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
import config


def main_menu_keyboard():
    """Main menu for users"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 تصفح الكورسات", callback_data="browse_courses")],
        [InlineKeyboardButton(text="🎬 مشترياتي", callback_data="my_purchases")],
    ])
    return keyboard


def courses_keyboard(courses):
    """Display all available courses"""
    buttons = []
    for course in courses:
        course_id, title, description, price = course
        buttons.append([InlineKeyboardButton(text=f"📖 {title}", callback_data=f"course_{course_id}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 رجوع", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def episodes_keyboard(episodes, course_id, user_id=None, purchased_episodes=None):
    """Display all episodes for a course"""
    buttons = []
    purchased_episodes = purchased_episodes or []
    
    for episode in episodes:
        episode_id, title, description, price, episode_number = episode
        
        # Check if user has purchased this episode
        is_purchased = episode_id in purchased_episodes
        
        if is_purchased:
            emoji = "✅"
            callback = f"watch_{episode_id}"
        else:
            emoji = "🔒"
            callback = f"buy_{episode_id}"
        
        button_text = f"{emoji} الحلقة {episode_number}: {title} - ${price:.2f}"
        buttons.append([InlineKeyboardButton(text=button_text, callback_data=callback)])
    
    buttons.append([InlineKeyboardButton(text="🔙 رجوع للكورسات", callback_data="browse_courses")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def purchase_confirmation_keyboard(episode_id):
    """Confirm purchase"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✅ تأكيد الشراء", callback_data=f"confirm_buy_{episode_id}")],
        [InlineKeyboardButton(text="❌ إلغاء", callback_data="cancel_purchase")],
    ])
    return keyboard


def video_access_keyboard(episode_id, user_id, token):
    """Create Web App button for video access"""
    webapp_url = f"{config.WEBAPP_URL}/watch?token={token}"
    
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="▶️ مشاهدة الفيديو", web_app=WebAppInfo(url=webapp_url))],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="my_purchases")],
    ])
    return keyboard


def my_purchases_keyboard(purchases):
    """Display user's purchased episodes"""
    buttons = []
    
    if not purchases:
        buttons.append([InlineKeyboardButton(text="📚 تصفح الكورسات", callback_data="browse_courses")])
    else:
        current_course = None
        for purchase in purchases:
            episode_id, episode_title, course_title, episode_number = purchase
            
            # Add course header if it's a new course
            if course_title != current_course:
                current_course = course_title
                buttons.append([InlineKeyboardButton(text=f"📖 {course_title}", callback_data="noop")])
            
            button_text = f"▶️ الحلقة {episode_number}: {episode_title}"
            buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"watch_{episode_id}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="back_to_main")])
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def back_to_main_keyboard():
    """Simple back button"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="back_to_main")],
    ])
    return keyboard
