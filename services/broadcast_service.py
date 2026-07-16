"""
broadcast_service.py
---------------------
Gerencia o agendamento (APScheduler) e o envio das mensagens de divulgação
automática das promoções para os grupos autorizados.
"""

import logging

from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.constants import ParseMode
from telegram.error import TelegramError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from services import promotion_service, group_service, product_service

logger = logging.getLogger("shop_bot.broadcast")


def _job_id(promotion_id: int) -> str:
    return f"promotion_{promotion_id}"


async def send_promotion(bot: Bot, promotion_id: int) -> None:
    """Envia a promoção para todos os grupos autorizados. Executado pelo APScheduler."""
    promotion = promotion_service.get_by_id(promotion_id)
    if promotion is None or not promotion.active:
        logger.info("Promoção %s inativa/removida — pulando envio.", promotion_id)
        return

    all_authorized = group_service.list_authorized()
    if not all_authorized:
        logger.info("Nenhum grupo autorizado no momento para a promoção %s.", promotion_id)
        return

    target_ids = promotion.target_group_id_list()
    if target_ids:
        groups = [g for g in all_authorized if g.id in target_ids]
        if not groups:
            logger.info("Nenhum dos grupos selecionados para a promoção %s está autorizado no momento.", promotion_id)
            return
    else:
        groups = all_authorized

    keyboard = None
    bot_username = bot.username
    if bot_username:
        deep_link = f"https://t.me/{bot_username}"
        if promotion.product_id:
            deep_link += f"?start=buy_{promotion.product_id}"
        keyboard = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🛒 Comprar Agora", url=deep_link)]]
        )

    for group in groups:
        try:
            if promotion.image_file_id and promotion.media_type == "video":
                await bot.send_video(
                    chat_id=group.chat_id,
                    video=promotion.image_file_id,
                    caption=promotion.text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                )
            elif promotion.image_file_id:
                await bot.send_photo(
                    chat_id=group.chat_id,
                    photo=promotion.image_file_id,
                    caption=promotion.text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                )
            else:
                await bot.send_message(
                    chat_id=group.chat_id,
                    text=promotion.text,
                    parse_mode=ParseMode.MARKDOWN,
                    reply_markup=keyboard,
                )
        except TelegramError as exc:
            logger.warning("Falha ao enviar promoção %s para o grupo %s: %s",
                            promotion_id, group.chat_id, exc)


def schedule_promotion(scheduler: AsyncIOScheduler, bot: Bot, promotion_id: int, interval_minutes: int) -> None:
    """Cria (ou substitui) o job periódico de uma promoção."""
    scheduler.add_job(
        send_promotion,
        trigger="interval",
        minutes=interval_minutes,
        args=[bot, promotion_id],
        id=_job_id(promotion_id),
        replace_existing=True,
        max_instances=1,
        coalesce=True,
    )
    logger.info("Promoção %s agendada a cada %s minutos.", promotion_id, interval_minutes)


def unschedule_promotion(scheduler: AsyncIOScheduler, promotion_id: int) -> None:
    """Remove o job de uma promoção, se existir."""
    job_id = _job_id(promotion_id)
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info("Agendamento da promoção %s removido.", promotion_id)


def load_and_schedule_active_promotions(scheduler: AsyncIOScheduler, bot: Bot) -> None:
    """Reagenda todas as promoções ativas ao iniciar o bot."""
    for promotion in promotion_service.list_active():
        schedule_promotion(scheduler, bot, promotion.id, promotion.interval_minutes)
