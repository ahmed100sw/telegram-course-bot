from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import user_kb
import config

router = Router()


class PurchaseStates(StatesGroup):
    waiting_for_receipt = State()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Handle /start command"""
    # Add user to database
    await db.add_user(
        user_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name
    )
    
    # Check if user is admin
    is_admin = await db.is_admin(message.from_user.id)
    
    welcome_text = f"مرحباً {message.from_user.first_name}! 👋\n\n"
    
    if is_admin:
        welcome_text += "🔑 أنت مسؤول النظام\n\n"
        welcome_text += "يمكنك استخدام الأوامر التالية:\n"
        welcome_text += "/admin - لوحة التحكم\n"
        welcome_text += "/start - القائمة الرئيسية\n\n"
    
    welcome_text += "اختر من القائمة أدناه:"
    
    await message.answer(welcome_text, reply_markup=user_kb.main_menu_keyboard())


@router.callback_query(F.data == "back_to_main")
async def back_to_main(callback: CallbackQuery):
    """Return to main menu"""
    is_admin = await db.is_admin(callback.from_user.id)
    
    welcome_text = f"مرحباً {callback.from_user.first_name}! 👋\n\n"
    
    if is_admin:
        welcome_text += "🔑 أنت مسؤول النظام\n\n"
    
    welcome_text += "اختر من القائمة أدناه:"
    
    await callback.message.edit_text(welcome_text, reply_markup=user_kb.main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "browse_courses")
async def browse_courses(callback: CallbackQuery):
    """Show all available courses"""
    courses = await db.get_all_courses()
    
    if not courses:
        await callback.message.edit_text(
            "📚 لا توجد كورسات متاحة حالياً.\n\nتابعنا للحصول على التحديثات!",
            reply_markup=user_kb.back_to_main_keyboard()
        )
    else:
        await callback.message.edit_text(
            "📚 الكورسات المتاحة:\n\nاختر كورس لعرض الحلقات:",
            reply_markup=user_kb.courses_keyboard(courses)
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("course_"))
async def show_course_episodes(callback: CallbackQuery):
    """Show episodes for a specific course"""
    course_id = int(callback.data.split("_")[1])
    
    # Get course info
    course = await db.get_course(course_id)
    if not course:
        await callback.answer("❌ الكورس غير موجود", show_alert=True)
        return
    
    course_id, title, description, price = course
    
    # Get episodes
    episodes = await db.get_course_episodes(course_id)
    
    if not episodes:
        await callback.message.edit_text(
            f"📖 {title}\n\n{description or 'لا يوجد وصف'}\n\n❌ لا توجد حلقات متاحة حالياً.",
            reply_markup=user_kb.back_to_main_keyboard()
        )
        await callback.answer()
        return
    
    # Get user's purchased episodes
    user_purchases = await db.get_user_purchases(callback.from_user.id)
    purchased_episode_ids = [p[0] for p in user_purchases]
    
    course_text = f"📖 {title}\n\n"
    if description:
        course_text += f"{description}\n\n"
    course_text += "اختر حلقة:"
    
    await callback.message.edit_text(
        course_text,
        reply_markup=user_kb.episodes_keyboard(episodes, course_id, callback.from_user.id, purchased_episode_ids)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy_"))
async def initiate_purchase(callback: CallbackQuery):
    """Initiate purchase process"""
    episode_id = int(callback.data.split("_")[1])
    
    # Get episode info
    episode = await db.get_episode(episode_id)
    if not episode:
        await callback.answer("❌ الحلقة غير موجودة", show_alert=True)
        return
    
    episode_id, course_id, title, description, video_path, price, episode_number = episode
    
    # Get course info
    course = await db.get_course(course_id)
    course_title = course[1] if course else "غير معروف"
    
    purchase_text = f"🛒 شراء حلقة\n\n"
    purchase_text += f"📖 الكورس: {course_title}\n"
    purchase_text += f"🎬 الحلقة {episode_number}: {title}\n"
    purchase_text += f"💰 السعر: ${price:.2f}\n\n"
    purchase_text += "هل تريد المتابعة؟"
    
    await callback.message.edit_text(
        purchase_text,
        reply_markup=user_kb.purchase_confirmation_keyboard(episode_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_buy_"))
async def confirm_purchase(callback: CallbackQuery, state: FSMContext):
    """Confirm purchase and request receipt"""
    episode_id = int(callback.data.split("_")[2])
    
    # Save episode_id in state
    await state.update_data(episode_id=episode_id)
    await state.set_state(PurchaseStates.waiting_for_receipt)
    
    payment_text = "💳 الدفع\n\n"
    payment_text += "يرجى إرسال صورة إيصال الدفع.\n\n"
    payment_text += "سيتم مراجعة الطلب من قبل الإدارة وسيتم إشعارك بالنتيجة."
    
    await callback.message.edit_text(payment_text)
    await callback.answer()


@router.callback_query(F.data == "cancel_purchase")
async def cancel_purchase(callback: CallbackQuery, state: FSMContext):
    """Cancel purchase"""
    await state.clear()
    await callback.message.edit_text(
        "❌ تم إلغاء عملية الشراء.",
        reply_markup=user_kb.back_to_main_keyboard()
    )
    await callback.answer()


@router.message(PurchaseStates.waiting_for_receipt, F.photo)
async def receive_receipt(message: Message, state: FSMContext):
    """Receive payment receipt photo"""
    data = await state.get_data()
    episode_id = data.get('episode_id')
    
    if not episode_id:
        await message.answer("❌ حدث خطأ. يرجى المحاولة مرة أخرى.")
        await state.clear()
        return
    
    # Get the largest photo
    photo = message.photo[-1]
    photo_id = photo.file_id
    
    # Create purchase request
    success = await db.create_purchase(message.from_user.id, episode_id, photo_id)
    
    if not success:
        await message.answer(
            "❌ لقد قمت بشراء هذه الحلقة مسبقاً أو لديك طلب معلق.",
            reply_markup=user_kb.back_to_main_keyboard()
        )
        await state.clear()
        return
    
    # Get episode info for notification
    episode = await db.get_episode(episode_id)
    episode_title = episode[2] if episode else "غير معروف"
    
    # Notify user
    await message.answer(
        "✅ تم استلام إيصال الدفع!\n\n"
        "سيتم مراجعة طلبك قريباً وسيتم إشعارك بالنتيجة.",
        reply_markup=user_kb.back_to_main_keyboard()
    )
    
    # Notify admin
    try:
        admin_text = f"🔔 طلب شراء جديد!\n\n"
        admin_text += f"👤 المستخدم: {message.from_user.first_name}"
        if message.from_user.username:
            admin_text += f" (@{message.from_user.username})"
        admin_text += f"\n🎬 الحلقة: {episode_title}\n"
        admin_text += f"💰 السعر: ${episode[5]:.2f}\n\n"
        admin_text += "استخدم /admin للمراجعة"
        
        from aiogram import Bot
        bot = message.bot
        await bot.send_photo(
            chat_id=config.ADMIN_ID,
            photo=photo_id,
            caption=admin_text
        )
    except Exception as e:
        print(f"Error notifying admin: {e}")
    
    await state.clear()


@router.callback_query(F.data == "my_purchases")
async def show_my_purchases(callback: CallbackQuery):
    """Show user's purchased episodes"""
    purchases = await db.get_user_purchases(callback.from_user.id)
    
    if not purchases:
        text = "🎬 مشترياتي\n\n"
        text += "ليس لديك أي مشتريات حتى الآن.\n\n"
        text += "تصفح الكورسات المتاحة وابدأ التعلم!"
    else:
        text = "🎬 مشترياتي\n\n"
        text += "اختر حلقة للمشاهدة:"
    
    await callback.message.edit_text(
        text,
        reply_markup=user_kb.my_purchases_keyboard(purchases)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("watch_"))
async def watch_episode(callback: CallbackQuery):
    """Generate token and show video access button"""
    episode_id = int(callback.data.split("_")[1])
    
    # Check if user has access
    has_access = await db.has_access(callback.from_user.id, episode_id)
    
    if not has_access:
        await callback.answer("❌ ليس لديك صلاحية لمشاهدة هذه الحلقة", show_alert=True)
        return
    
    # Get episode info
    episode = await db.get_episode(episode_id)
    if not episode:
        await callback.answer("❌ الحلقة غير موجودة", show_alert=True)
        return
    
    episode_id, course_id, title, description, video_path, price, episode_number = episode
    
    # Generate access token
    token = await db.create_video_token(callback.from_user.id, episode_id)
    
    watch_text = f"▶️ مشاهدة الحلقة\n\n"
    watch_text += f"🎬 {title}\n\n"
    if description:
        watch_text += f"{description}\n\n"
    watch_text += "⚠️ ملاحظة: الرابط صالح لمدة 24 ساعة فقط.\n"
    watch_text += "يمكنك المشاهدة فقط من تطبيق تلغرام على الهاتف."
    
    await callback.message.edit_text(
        watch_text,
        reply_markup=user_kb.video_access_keyboard(episode_id, callback.from_user.id, token)
    )
    await callback.answer()


@router.callback_query(F.data == "noop")
async def noop_callback(callback: CallbackQuery):
    """No operation callback for headers"""
    await callback.answer()
