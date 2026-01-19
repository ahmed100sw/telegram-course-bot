from aiogram import Router, F
from aiogram.types import CallbackQuery
from database import db
from keyboards import admin_kb
import config

router = Router()


async def is_admin_check(user_id: int) -> bool:
    """Check if user is admin"""
    return await db.is_admin(user_id)


@router.callback_query(F.data == "admin_pending_purchases")
async def show_pending_purchases(callback: CallbackQuery):
    """Show all pending purchase requests"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    purchases = await db.get_pending_purchases()
    
    text = "💰 طلبات الشراء المعلقة\n\n"
    
    if not purchases:
        text += "✅ لا توجد طلبات معلقة حالياً."
    else:
        text += f"عدد الطلبات: {len(purchases)}\n\n"
        text += "اختر طلب للمراجعة:"
    
    await callback.message.edit_text(
        text,
        reply_markup=admin_kb.pending_purchases_keyboard(purchases)
    )
    await callback.answer()


@router.callback_query(F.data.startswith("review_payment_"))
async def review_payment(callback: CallbackQuery):
    """Review a specific payment request"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    purchase_id = int(callback.data.split("_")[2])
    
    # Get purchase details
    purchases = await db.get_pending_purchases()
    purchase = None
    for p in purchases:
        if p[0] == purchase_id:
            purchase = p
            break
    
    if not purchase:
        await callback.answer("❌ الطلب غير موجود", show_alert=True)
        return
    
    purchase_id, user_id, episode_id, receipt_photo, username, episode_title, price = purchase
    
    user_display = username if username else f"User {user_id}"
    
    text = f"💳 مراجعة طلب الشراء\n\n"
    text += f"👤 المستخدم: {user_display}\n"
    text += f"🎬 الحلقة: {episode_title}\n"
    text += f"💰 السعر: ${price:.2f}\n\n"
    text += "الإيصال المرفق أدناه:"
    
    # Send receipt photo with approval buttons
    await callback.message.delete()
    
    await callback.bot.send_photo(
        chat_id=callback.from_user.id,
        photo=receipt_photo,
        caption=text,
        reply_markup=admin_kb.payment_verification_keyboard(purchase_id)
    )
    
    await callback.answer()


@router.callback_query(F.data.startswith("approve_payment_"))
async def approve_payment(callback: CallbackQuery):
    """Approve a payment request"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    purchase_id = int(callback.data.split("_")[2])
    
    # Get purchase info before approval
    purchase = await db.get_purchase(purchase_id)
    if not purchase:
        await callback.answer("❌ الطلب غير موجود", show_alert=True)
        return
    
    purchase_id, user_id, episode_id, payment_status = purchase
    
    if payment_status != 'pending':
        await callback.answer("❌ تم معالجة هذا الطلب مسبقاً", show_alert=True)
        return
    
    # Approve purchase
    await db.approve_purchase(purchase_id)
    
    # Get episode info
    episode = await db.get_episode(episode_id)
    episode_title = episode[2] if episode else "غير معروف"
    
    # Notify user
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=f"✅ تم قبول طلب الشراء!\n\n"
                 f"🎬 الحلقة: {episode_title}\n\n"
                 f"يمكنك الآن مشاهدة الحلقة من قسم 'مشترياتي'."
        )
    except Exception as e:
        print(f"Error notifying user: {e}")
    
    await callback.message.edit_caption(
        caption=f"✅ تم قبول الطلب بنجاح!\n\n"
                f"تم إشعار المستخدم.",
        reply_markup=admin_kb.back_to_admin_keyboard()
    )
    await callback.answer("✅ تم قبول الطلب")


@router.callback_query(F.data.startswith("reject_payment_"))
async def reject_payment(callback: CallbackQuery):
    """Reject a payment request"""
    if not await is_admin_check(callback.from_user.id):
        await callback.answer("❌ غير مصرح لك", show_alert=True)
        return
    
    purchase_id = int(callback.data.split("_")[2])
    
    # Get purchase info before rejection
    purchase = await db.get_purchase(purchase_id)
    if not purchase:
        await callback.answer("❌ الطلب غير موجود", show_alert=True)
        return
    
    purchase_id, user_id, episode_id, payment_status = purchase
    
    if payment_status != 'pending':
        await callback.answer("❌ تم معالجة هذا الطلب مسبقاً", show_alert=True)
        return
    
    # Reject purchase
    await db.reject_purchase(purchase_id)
    
    # Get episode info
    episode = await db.get_episode(episode_id)
    episode_title = episode[2] if episode else "غير معروف"
    
    # Notify user
    try:
        await callback.bot.send_message(
            chat_id=user_id,
            text=f"❌ تم رفض طلب الشراء\n\n"
                 f"🎬 الحلقة: {episode_title}\n\n"
                 f"يرجى التواصل مع الإدارة للمزيد من المعلومات."
        )
    except Exception as e:
        print(f"Error notifying user: {e}")
    
    await callback.message.edit_caption(
        caption=f"❌ تم رفض الطلب\n\n"
                f"تم إشعار المستخدم.",
        reply_markup=admin_kb.back_to_admin_keyboard()
    )
    await callback.answer("❌ تم رفض الطلب")
