from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards import admin_kb, user_kb
import config

router = Router()


class CourseStates(StatesGroup):
    waiting_for_course_title = State()
    waiting_for_course_description = State()
    waiting_for_course_price = State()


class EpisodeStates(StatesGroup):
    waiting_for_episode_number = State()
    waiting_for_episode_title = State()
    waiting_for_episode_description = State()
    waiting_for_episode_price = State()
    waiting_for_episode_video = State()


async def is_admin_check(user_id: int) -> bool:
    """Check if user is admin"""
    return await db.is_admin(user_id)


@router.message(Command("admin"))
async def cmd_admin(message: Message):
    """Admin panel command"""
    if not await is_admin_check(message.from_user.id):
        await message.answer("❌ هذا الأمر متاح للمسؤولين فقط.")
        return
    
    await message.answer(
        "🔑 لوحة التحكم\n\nاختر من القائمة:",
        reply_markup=admin_kb.admin_main_menu_keyboard()
    )


@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery):
    """Show admin panel"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    await callback.message.edit_text(
        "🔑 لوحة التحكم\n\nاختر من القائمة:",
        reply_markup=admin_kb.admin_main_menu_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_courses")
async def show_admin_courses(callback: CallbackQuery):
    """Show courses management"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    courses = await db.get_all_courses()
    
    text = "📚 إدارة الكورسات\n\n"
    if courses:
        text += f"عدد الكورسات: {len(courses)}"
    else:
        text += "لا توجد كورسات. أضف كورس جديد!"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_kb.admin_courses_keyboard(courses)
    )
    await callback.answer()


@router.callback_query(F.data == "admin_add_course")
async def add_course_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a new course"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    await callback.message.edit_text("📝 أدخل عنوان الكورس:")
    await state.set_state(CourseStates.waiting_for_course_title)
    await callback.answer()


@router.message(CourseStates.waiting_for_course_title)
async def receive_course_title(message: Message, state: FSMContext):
    """Receive course title"""
    await state.update_data(title=message.text)
    await state.set_state(CourseStates.waiting_for_course_description)
    await message.answer("📝 أدخل وصف الكورس (أو أرسل '-' للتخطي):")


@router.message(CourseStates.waiting_for_course_description)
async def receive_course_description(message: Message, state: FSMContext):
    """Receive course description"""
    description = None if message.text == '-' else message.text
    await state.update_data(description=description)
    await state.set_state(CourseStates.waiting_for_course_price)
    await message.answer("💰 أدخل سعر الكورس الكامل (أو 0 إذا كان مجاني):")


@router.message(CourseStates.waiting_for_course_price)
async def receive_course_price(message: Message, state: FSMContext):
    """Receive course price and create course"""
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح:")
        return
    
    data = await state.get_data()
    title = data['title']
    description = data.get('description')
    
    # Create course
    course_id = await db.add_course(title, description, price)
    
    await message.answer(
        f"✅ تم إضافة الكورس بنجاح!\n\n"
        f"📖 {title}\n"
        f"💰 السعر: ${price:.2f}\n\n"
        f"يمكنك الآن إضافة حلقات للكورس.",
        reply_markup=admin_kb.back_to_admin_keyboard()
    )
    
    await state.clear()


@router.callback_query(F.data.startswith("admin_course_"))
async def show_course_detail(callback: CallbackQuery):
    """Show course details and episodes"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    course_id = int(callback.data.split("_")[2])
    
    course = await db.get_course(course_id)
    if not course:
        await callback.answer("❌ الكورس غير موجود", show_alert=True)
        return
    
    course_id, title, description, price = course
    episodes = await db.get_course_episodes(course_id)
    
    text = f"📖 {title}\n\n"
    if description:
        text += f"{description}\n\n"
    text += f"💰 السعر: ${price:.2f}\n"
    text += f"🎬 عدد الحلقات: {len(episodes)}\n\n"
    text += "إدارة الحلقات:"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_kb.admin_course_detail_keyboard(course_id, episodes)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_add_episode_"))
async def add_episode_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a new episode"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    course_id = int(callback.data.split("_")[3])
    
    await state.update_data(course_id=course_id)
    await state.set_state(EpisodeStates.waiting_for_episode_number)
    
    await callback.message.edit_text("🔢 أدخل رقم الحلقة:")
    await callback.answer()


@router.message(EpisodeStates.waiting_for_episode_number)
async def receive_episode_number(message: Message, state: FSMContext):
    """Receive episode number"""
    try:
        episode_number = int(message.text)
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح:")
        return
    
    await state.update_data(episode_number=episode_number)
    await state.set_state(EpisodeStates.waiting_for_episode_title)
    await message.answer("📝 أدخل عنوان الحلقة:")


@router.message(EpisodeStates.waiting_for_episode_title)
async def receive_episode_title(message: Message, state: FSMContext):
    """Receive episode title"""
    await state.update_data(title=message.text)
    await state.set_state(EpisodeStates.waiting_for_episode_description)
    await message.answer("📝 أدخل وصف الحلقة (أو أرسل '-' للتخطي):")


@router.message(EpisodeStates.waiting_for_episode_description)
async def receive_episode_description(message: Message, state: FSMContext):
    """Receive episode description"""
    description = None if message.text == '-' else message.text
    await state.update_data(description=description)
    await state.set_state(EpisodeStates.waiting_for_episode_price)
    await message.answer("💰 أدخل سعر الحلقة:")


@router.message(EpisodeStates.waiting_for_episode_price)
async def receive_episode_price(message: Message, state: FSMContext):
    """Receive episode price"""
    try:
        price = float(message.text)
    except ValueError:
        await message.answer("❌ يرجى إدخال رقم صحيح:")
        return
    
    await state.update_data(price=price)
    await state.set_state(EpisodeStates.waiting_for_episode_video)
    await message.answer("🎬 أرسل ملف الفيديو:")


@router.message(EpisodeStates.waiting_for_episode_video, F.video)
async def receive_episode_video(message: Message, state: FSMContext):
    """Receive episode video and create episode"""
    video = message.video
    video_id = video.file_id
    
    data = await state.get_data()
    course_id = data['course_id']
    episode_number = data['episode_number']
    title = data['title']
    description = data.get('description')
    price = data['price']
    
    # Save video file_id as path (we'll use file_id to send video)
    video_path = video_id
    
    # Create episode
    episode_id = await db.add_episode(
        course_id=course_id,
        title=title,
        description=description,
        video_path=video_path,
        price=price,
        episode_number=episode_number
    )
    
    await message.answer(
        f"✅ تم إضافة الحلقة بنجاح!\n\n"
        f"🎬 الحلقة {episode_number}: {title}\n"
        f"💰 السعر: ${price:.2f}",
        reply_markup=admin_kb.back_to_admin_keyboard()
    )
    
    await state.clear()


@router.callback_query(F.data.startswith("admin_delete_course_"))
async def confirm_delete_course(callback: CallbackQuery):
    """Confirm course deletion"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    course_id = int(callback.data.split("_")[3])
    
    course = await db.get_course(course_id)
    if not course:
        await callback.answer("❌ الكورس غير موجود", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"⚠️ هل أنت متأكد من حذف الكورس '{course[1]}'?\n\n"
        f"سيتم حذف جميع الحلقات المرتبطة به!",
        reply_markup=admin_kb.confirm_delete_keyboard("course", course_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_course_"))
async def delete_course(callback: CallbackQuery):
    """Delete course"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    course_id = int(callback.data.split("_")[3])
    
    await db.delete_course(course_id)
    
    await callback.message.edit_text(
        "✅ تم حذف الكورس بنجاح!",
        reply_markup=admin_kb.back_to_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("cancel_delete_"))
async def cancel_delete(callback: CallbackQuery):
    """Cancel deletion"""
    await callback.message.edit_text(
        "❌ تم إلغاء الحذف.",
        reply_markup=admin_kb.back_to_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data.startswith("admin_delete_episode_"))
async def confirm_delete_episode(callback: CallbackQuery):
    """Confirm episode deletion"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    episode_id = int(callback.data.split("_")[3])
    
    episode = await db.get_episode(episode_id)
    if not episode:
        await callback.answer("❌ الحلقة غير موجودة", show_alert=True)
        return
    
    await callback.message.edit_text(
        f"⚠️ هل أنت متأكد من حذف الحلقة '{episode[2]}'?",
        reply_markup=admin_kb.confirm_delete_keyboard("episode", episode_id)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("confirm_delete_episode_"))
async def delete_episode(callback: CallbackQuery):
    """Delete episode"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    episode_id = int(callback.data.split("_")[3])
    
    await db.delete_episode(episode_id)
    
    await callback.message.edit_text(
        "✅ تم حذف الحلقة بنجاح!",
        reply_markup=admin_kb.back_to_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_users")
async def show_users(callback: CallbackQuery):
    """Show all users"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    users = await db.get_all_users()
    
    text = "👥 المستخدمين\n\n"
    text += f"عدد المستخدمين: {len(users)}\n\n"
    
    for user in users[:20]:  # Show first 20 users
        user_id, username, first_name, is_admin, created_at = user
        admin_badge = "🔑 " if is_admin else ""
        username_display = f"@{username}" if username else f"ID: {user_id}"
        text += f"{admin_badge}{first_name} ({username_display})\n"
    
    if len(users) > 20:
        text += f"\n... و {len(users) - 20} مستخدم آخر"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_kb.back_to_admin_keyboard()
    )
    await callback.answer()


@router.callback_query(F.data == "admin_stats")
async def show_stats(callback: CallbackQuery):
    """Show bot statistics"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    stats = await db.get_stats()
    
    text = "📊 الإحصائيات\n\n"
    text += f"👥 إجمالي المستخدمين: {stats['total_users']}\n"
    text += f"📚 إجمالي الكورسات: {stats['total_courses']}\n"
    text += f"🎬 إجمالي الحلقات: {stats['total_episodes']}\n"
    text += f"✅ إجمالي المبيعات: {stats['total_sales']}\n"
    text += f"⏳ طلبات معلقة: {stats['pending_purchases']}\n"
    text += f"💰 إجمالي الإيرادات: ${stats['total_revenue']:.2f}"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_kb.back_to_admin_keyboard()
    )
    await callback.answer()
