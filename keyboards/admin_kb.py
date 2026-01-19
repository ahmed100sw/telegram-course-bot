from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_main_menu_keyboard():
    """Admin panel main menu"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📚 إدارة الكورسات", callback_data="admin_courses")],
        [InlineKeyboardButton(text="💰 طلبات الشراء المعلقة", callback_data="admin_pending_purchases")],
        [InlineKeyboardButton(text="👥 المستخدمين", callback_data="admin_users")],
        [InlineKeyboardButton(text="📊 الإحصائيات", callback_data="admin_stats")],
        [InlineKeyboardButton(text="🔙 القائمة الرئيسية", callback_data="back_to_main")],
    ])
    return keyboard


def admin_courses_keyboard(courses):
    """Admin courses management"""
    buttons = []
    
    for course in courses:
        course_id, title, description, price = course
        buttons.append([
            InlineKeyboardButton(text=f"📖 {title}", callback_data=f"admin_course_{course_id}"),
            InlineKeyboardButton(text="🗑️", callback_data=f"admin_delete_course_{course_id}")
        ])
    
    buttons.append([InlineKeyboardButton(text="➕ إضافة كورس جديد", callback_data="admin_add_course")])
    buttons.append([InlineKeyboardButton(text="🔙 لوحة التحكم", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def admin_course_detail_keyboard(course_id, episodes):
    """Admin course detail with episodes"""
    buttons = []
    
    for episode in episodes:
        episode_id, title, description, price, episode_number = episode
        buttons.append([
            InlineKeyboardButton(text=f"الحلقة {episode_number}: {title}", callback_data=f"admin_episode_{episode_id}"),
            InlineKeyboardButton(text="🗑️", callback_data=f"admin_delete_episode_{episode_id}")
        ])
    
    buttons.append([InlineKeyboardButton(text="➕ إضافة حلقة جديدة", callback_data=f"admin_add_episode_{course_id}")])
    buttons.append([InlineKeyboardButton(text="🔙 رجوع للكورسات", callback_data="admin_courses")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_verification_keyboard(purchase_id):
    """Approve or reject payment"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ قبول", callback_data=f"approve_payment_{purchase_id}"),
            InlineKeyboardButton(text="❌ رفض", callback_data=f"reject_payment_{purchase_id}")
        ],
        [InlineKeyboardButton(text="🔙 رجوع", callback_data="admin_pending_purchases")]
    ])
    return keyboard


def pending_purchases_keyboard(purchases):
    """Display pending purchases for admin"""
    buttons = []
    
    if not purchases:
        buttons.append([InlineKeyboardButton(text="✅ لا توجد طلبات معلقة", callback_data="noop")])
    else:
        for purchase in purchases:
            purchase_id, user_id, episode_id, receipt_photo, username, episode_title, price = purchase
            user_display = username if username else f"User {user_id}"
            button_text = f"👤 {user_display} - {episode_title} (${price:.2f})"
            buttons.append([InlineKeyboardButton(text=button_text, callback_data=f"review_payment_{purchase_id}")])
    
    buttons.append([InlineKeyboardButton(text="🔙 لوحة التحكم", callback_data="admin_panel")])
    
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def confirm_delete_keyboard(item_type, item_id):
    """Confirm deletion"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ تأكيد الحذف", callback_data=f"confirm_delete_{item_type}_{item_id}"),
            InlineKeyboardButton(text="❌ إلغاء", callback_data=f"cancel_delete_{item_type}_{item_id}")
        ]
    ])
    return keyboard


def back_to_admin_keyboard():
    """Back to admin panel"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔙 لوحة التحكم", callback_data="admin_panel")]
    ])
    return keyboard
